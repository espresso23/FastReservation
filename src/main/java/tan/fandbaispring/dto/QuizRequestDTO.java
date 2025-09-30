package tan.fandbaispring.dto;

import lombok.Data;
import java.util.Map;
import com.fasterxml.jackson.annotation.JsonProperty;

@Data
public class QuizRequestDTO {
    @JsonProperty("userPrompt")
    private String userPrompt;
    // Chứa các tham số đã thu thập được (ví dụ: {style: "lãng mạn"})
    @JsonProperty("currentParams")
    private Map<String, Object> currentParams;
}