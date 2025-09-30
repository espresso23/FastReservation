package tan.fandbaispring.dto;

import lombok.Data;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Map;

@Data
public class ImageOptionDTO {
    private String label;

    @JsonProperty("image_url")
    private String imageUrl;

    private String value;

    // Thông số gợi ý thêm từ hình ảnh (ví dụ: style_vibe, has_balcony ...)
    private Map<String, Object> params;
}


