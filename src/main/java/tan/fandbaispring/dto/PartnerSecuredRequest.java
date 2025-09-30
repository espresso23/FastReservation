package tan.fandbaispring.dto;

import lombok.Data;

@Data
class PartnerSecuredRequest {
    private String ownerId;
    // Có thể thêm email/password nếu muốn xác thực đầy đủ hơn mỗi lần gọi
}