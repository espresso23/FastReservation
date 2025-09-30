package tan.fandbaispring.dto;

import lombok.Data;
import com.fasterxml.jackson.annotation.JsonProperty;

@Data
public class SearchResultDTO {
    @JsonProperty("establishment_id")
    private String establishmentId;

    @JsonProperty("relevance_score")
    private float relevanceScore;
}