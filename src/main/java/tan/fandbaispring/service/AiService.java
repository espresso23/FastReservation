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

    // RestTemplate thường được khuyến nghị tạo Bean hoặc dùng WebClient,
    // nhưng dùng instance này là đủ cho Hackathon
    private final RestTemplate restTemplate = new RestTemplate();

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

            // Heuristic nhẹ: nếu prompt có chứa "lãng mạn" thì set style_vibe
            Map<String, Object> params = request.getCurrentParams() != null
                    ? new java.util.HashMap<>(request.getCurrentParams())
                    : new java.util.HashMap<>();
            String prompt = request.getUserPrompt() != null ? request.getUserPrompt().toLowerCase() : "";
            if (!params.containsKey("style_vibe") && prompt.contains("lãng mạn")) {
                params.put("style_vibe", "romantic");
            }

            String[] order = new String[]{
                    "city", "check_in_date", "style_vibe", "max_price",
                    "travel_companion", "duration", "amenities_priority"
            };
            java.util.Map<String, String> questions = java.util.Map.of(
                    "city", "Bạn muốn đi ở thành phố nào?",
                    "check_in_date", "Bạn dự định ngày bắt đầu chuyến đi là khi nào? (YYYY-MM-DD)",
                    "style_vibe", "Bạn thích phong cách/không khí nào? (ví dụ: lãng mạn, yên tĩnh, sôi động)",
                    "max_price", "Ngân sách tối đa của bạn là bao nhiêu (VND)?",
                    "travel_companion", "Bạn đi cùng ai? (một mình, cặp đôi, gia đình, bạn bè)",
                    "duration", "Thời lượng chuyến đi bao lâu? (số ngày)",
                    "amenities_priority", "Bạn ưu tiên tiện ích nào? (ví dụ: hồ bơi, spa, bãi đậu xe)"
            );

            String missing = null;
            for (String key : order) {
                Object v = params.get(key);
                if (v == null || (v instanceof String && ((String) v).isBlank())) {
                    missing = key;
                    break;
                }
            }

            if (missing != null) {
                fallback.setQuizCompleted(false);
                fallback.setKeyToCollect(missing);
                fallback.setMissingQuiz(questions.get(missing));
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

        // Sử dụng exchange để xử lý List<Object> trả về
        ResponseEntity<List<SearchResultDTO>> response = restTemplate.exchange(
                url,
                HttpMethod.POST,
                new org.springframework.http.HttpEntity<>(request),
                new ParameterizedTypeReference<List<SearchResultDTO>>() {}
        );

        return response.getBody() != null ? response.getBody() : Collections.emptyList();
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
}