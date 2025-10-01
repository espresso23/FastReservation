package tan.fandbaispring.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import tan.fandbaispring.dto.QuizRequestDTO;
import tan.fandbaispring.dto.QuizResponseDTO;
import tan.fandbaispring.dto.SearchRequestDTO;
import tan.fandbaispring.dto.SearchResultDTO;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import java.util.Collections;
import java.util.List;
import java.util.Map;

@Service
public class AiService {

    @Value("${python.ai.service.url}")
    private String pythonAiServiceUrl;

    // RestTemplate với timeout để tránh chờ quá lâu nếu Python service treo
    private final RestTemplate restTemplate;

    public AiService() {
        org.springframework.http.client.SimpleClientHttpRequestFactory f = new org.springframework.http.client.SimpleClientHttpRequestFactory();
        f.setConnectTimeout(3000); // 3s
        f.setReadTimeout(3000);    // 3s
        this.restTemplate = new RestTemplate(f);
    }

    /**
     * Gọi Python API để sinh câu hỏi Quiz có điều kiện.
     * @param request Chứa prompt người dùng và các tham số đã thu thập.
     * @return QuizResponseDTO chứa câu hỏi tiếp theo hoặc kết quả hoàn chỉnh.
     */
    public QuizResponseDTO generateQuiz(QuizRequestDTO request) {
        String url = pythonAiServiceUrl + "/generate-quiz";
        try {
            // Gọi Python service bình thường
            return restTemplate.postForObject(url, request, QuizResponseDTO.class);
        } catch (Exception ex) {
            // Fallback nội bộ khi Python trả 5xx hoặc không khả dụng
            QuizResponseDTO fallback = new QuizResponseDTO();

            // Heuristic nhẹ: nếu prompt có chứa "lãng mạn" thì gộp vào amenities_priority
            Map<String, Object> params = request.getCurrentParams() != null
                    ? new java.util.HashMap<>(request.getCurrentParams())
                    : new java.util.HashMap<>();
            String prompt = request.getUserPrompt() != null ? request.getUserPrompt().toLowerCase() : "";

            // Thứ tự câu hỏi mặc định (Hotel). Với Restaurant sẽ bỏ qua 'duration'
            java.util.List<String> orderList = new java.util.ArrayList<>(java.util.Arrays.asList(
                    "city", "check_in_date", "max_price",
                    "travel_companion", "duration", "amenities_priority"
            ));
            try {
                Object typeObj = params.get("establishment_type");
                if (typeObj != null && "RESTAURANT".equalsIgnoreCase(String.valueOf(typeObj))) {
                    orderList.remove("duration");
                }
            } catch (Exception ignore) {}
            java.util.Map<String, String> questions = java.util.Map.of(
                    "city", "Bạn muốn đi ở thành phố nào?",
                    "check_in_date", "Bạn dự định ngày bắt đầu chuyến đi là khi nào? (YYYY-MM-DD)",
                    "max_price", "Ngân sách tối đa của bạn là bao nhiêu (VND)?",
                    "travel_companion", "Bạn đi cùng ai? (một mình, cặp đôi, gia đình, bạn bè)",
                    "duration", "Thời lượng chuyến đi bao lâu? (số ngày)",
                    "amenities_priority", "Bạn ưu tiên tiện ích nào? (ví dụ: hồ bơi, spa, bãi đậu xe)"
            );

            String missing = null;
            for (String key : orderList) {
                Object v = params.get(key);
                if (v == null || (v instanceof String && ((String) v).isBlank())) {
                    missing = key;
                    // Ưu tiên hỏi loại cơ sở nếu đã có city nhưng thiếu establishment_type
                    if ("city".equals(key) && params.get("city") != null && params.get("establishment_type") == null) {
                        missing = "establishment_type";
                    }
                    break;
                }
                // Cho phép hỏi thêm tiện ích một lần ngay cả khi đã chọn
                if ("amenities_priority".equals(key)) {
                    boolean confirmed = Boolean.TRUE.equals(params.get("_amenities_confirmed"));
                    if (!confirmed && v != null && !String.valueOf(v).isBlank()) {
                        missing = key; // hỏi thêm lần nữa
                        // đặt cờ để lần sau không hỏi lại
                        params.put("_amenities_confirmed", true);
                        break;
                    }
                }
            }

            if (missing != null) {
                fallback.setQuizCompleted(false);
                fallback.setKeyToCollect(missing);
                // thay đổi câu hỏi nếu đang ở bước tiện ích và người dùng đã có lựa chọn trước đó
                if ("amenities_priority".equals(missing) && request.getCurrentParams() != null && request.getCurrentParams().get("amenities_priority") != null) {
                    fallback.setMissingQuiz("Bạn có muốn chọn thêm tiện ích không? (bạn có thể bỏ qua nếu đủ)");
                } else {
                    fallback.setMissingQuiz(questions.get(missing));
                }
                fallback.setFinalParams(params);
            } else {
                fallback.setQuizCompleted(true);
                fallback.setFinalParams(params);
            }
            return fallback;
        }
    }

    /**
     * Gọi Python API để thực hiện RAG Search.
     * @param params Map chứa các tham số hoàn chỉnh (style, max_price, v.v.).
     * @return List<SearchResultDTO> chứa ID và điểm relevance score.
     */
    public List<SearchResultDTO> performRagSearch(Map<String, Object> params) {
        String url = pythonAiServiceUrl + "/rag-search";

        // Bọc params vào SearchRequestDTO để match với Pydantic model bên Python
        SearchRequestDTO request = new SearchRequestDTO();
        request.setParams(params);

        try {
            // Sử dụng exchange để xử lý List<Object> trả về
            ResponseEntity<List<SearchResultDTO>> response = restTemplate.exchange(
                    url,
                    HttpMethod.POST,
                    new org.springframework.http.HttpEntity<>(request),
                    new ParameterizedTypeReference<List<SearchResultDTO>>() {}
            );

            return response.getBody() != null ? response.getBody() : Collections.emptyList();
        } catch (Exception ex) {
            // Timeout hoặc lỗi mạng → trả rỗng để controller fallback sang tìm kiếm nội bộ
            return Collections.emptyList();
        }
    }

    /**
     * Gọi Python API để cập nhật Vector Store khi có cơ sở mới được tạo.
     * @param establishmentId ID của cơ sở mới vừa được lưu vào PostgreSQL.
     */
    public void processNewEstablishment(String establishmentId) {
        String url = pythonAiServiceUrl + "/add-establishment";

        // Retry tối đa 3 lần, chờ 500ms giữa các lần (phòng trường hợp DB chưa kịp thấy bản ghi)
        int attempts = 0;
        while (attempts < 3) {
            try {
                restTemplate.postForObject(url, Map.of("id", establishmentId), Void.class);
                return; // thành công
            } catch (Exception e) {
                attempts++;
                if (attempts >= 3) {
                    System.err.println("LỖI: Không thể cập nhật Vector Store cho ID " + establishmentId +
                            ". Lần thử: " + attempts + ", lỗi: " + e.getMessage());
                    return;
                }
                try { Thread.sleep(500); } catch (InterruptedException ignored) {}
            }
        }
    }

    /**
     * Đảm bảo gọi index sau khi transaction DB đã COMMIT.
     * Nếu không có transaction, gọi ngay lập tức.
     */
    public void indexEstablishmentAfterCommit(String establishmentId) {
        if (TransactionSynchronizationManager.isSynchronizationActive()) {
            TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
                @Override
                public void afterCommit() {
                    processNewEstablishment(establishmentId);
                }
            });
        } else {
            processNewEstablishment(establishmentId);
        }
    }

    /**
     * Cập nhật cơ sở trong Vector Store khi có thay đổi thông tin.
     * @param establishmentId ID của cơ sở cần cập nhật.
     */
    public void updateEstablishmentInVectorStore(String establishmentId) {
        String url = pythonAiServiceUrl + "/add-establishment";

        // Retry tối đa 3 lần, chờ 500ms giữa các lần
        int attempts = 0;
        while (attempts < 3) {
            try {
                restTemplate.postForObject(url, Map.of("id", establishmentId), Void.class);
                return; // thành công
            } catch (Exception e) {
                attempts++;
                if (attempts >= 3) {
                    System.err.println("LỖI: Không thể cập nhật Vector Store cho ID " + establishmentId +
                            ". Lần thử: " + attempts + ", lỗi: " + e.getMessage());
                    return;
                }
                try { Thread.sleep(500); } catch (InterruptedException ignored) {}
            }
        }
    }

    /**
     * Xóa cơ sở khỏi Vector Store.
     * @param establishmentId ID của cơ sở cần xóa.
     */
    public void removeEstablishmentFromVectorStore(String establishmentId) {
        String url = pythonAiServiceUrl + "/remove-establishment";

        try {
            restTemplate.postForObject(url, Map.of("id", establishmentId), Void.class);
        } catch (Exception e) {
            System.err.println("LỖI: Không thể xóa khỏi Vector Store cho ID " + establishmentId +
                    ". Lỗi: " + e.getMessage());
        }
    }
}