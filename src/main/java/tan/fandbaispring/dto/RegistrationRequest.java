package tan.fandbaispring.dto;

import lombok.Data;

@Data
public class RegistrationRequest {
    private String email;
    private String password; // Trong demo sẽ là '123456'
    private String role;     // "CUSTOMER" hoặc "PARTNER"
}