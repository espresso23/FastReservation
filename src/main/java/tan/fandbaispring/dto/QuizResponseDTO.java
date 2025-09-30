package tan.fandbaispring.dto;

import lombok.Data;
import java.util.Map;
import java.util.List;
import com.fasterxml.jackson.annotation.JsonProperty;

@Data
public class QuizResponseDTO {
    @JsonProperty("quiz_completed")
    private boolean quizCompleted;

    @JsonProperty("missing_quiz")
    private String missingQuiz;
    // Key của tham số cần thu thập tiếp theo (ví dụ: "max_price")
    @JsonProperty("key_to_collect")
    private String keyToCollect;
    // Bộ tham số hoàn chỉnh nếu quizCompleted là true
    @JsonProperty("final_params")
    private Map<String, Object> finalParams;

    // Danh sách lựa chọn đề xuất (nếu có) cho keyToCollect
    @JsonProperty("options")
    private List<String> options;

    // Các lựa chọn dạng thẻ ảnh
    @JsonProperty("image_options")
    private List<ImageOptionDTO> imageOptions;
}