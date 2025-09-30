package tan.fandbaispring.dto;

import java.util.Map;
import com.fasterxml.jackson.annotation.JsonProperty;

public class SearchRequestDTO {

    @JsonProperty("params")
    private Map<String, Object> params;

    public Map<String, Object> getParams() {
        return params;
    }

    public void setParams(Map<String, Object> params) {
        this.params = params;
    }
}