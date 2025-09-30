package tan.fandbaispring.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import tan.fandbaispring.dto.LoginRequest;
import tan.fandbaispring.dto.RegistrationRequest;
import tan.fandbaispring.model.User;
import tan.fandbaispring.model.UserRole;
import tan.fandbaispring.repository.UserRepository;
import tan.fandbaispring.service.AuthService;

import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @Autowired
    private UserRepository userRepository;
    @Autowired
    private AuthService authService;

    /**
     * API Đăng ký đơn giản cho cả CUSTOMER và PARTNER.
     */
    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody RegistrationRequest req) {
        if (userRepository.findByEmail(req.getEmail()).isPresent()) {
            return ResponseEntity.status(HttpStatus.CONFLICT).body(Map.of("message", "Email đã tồn tại."));
        }

        User newUser = new User();
        newUser.setEmail(req.getEmail());
        newUser.setPasswordHash("123456"); // Mật khẩu cứng

        try {
            // Đảm bảo vai trò được truyền đúng (CUSTOMER hoặc PARTNER)
            newUser.setRole(UserRole.valueOf(req.getRole().toUpperCase()));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("message", "Vai trò không hợp lệ."));
        }

        User savedUser = userRepository.save(newUser);

        return ResponseEntity.status(HttpStatus.CREATED).body(
                Map.of("id", savedUser.getId(), "email", savedUser.getEmail(), "role", savedUser.getRole(), "message", "Đăng ký thành công.")
        );
    }

    /**
     * API Đăng nhập đơn thuần (Stateless).
     * Trả về ID và Role của người dùng đã xác thực.
     */
    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody LoginRequest req) {
        Optional<User> userOpt;

        // Thử xác thực là PARTNER trước (Ưu tiên quản trị)
        userOpt = authService.authenticatePartner(req.getEmail(), req.getPassword());

        // Nếu không phải Partner, thử xác thực là CUSTOMER
        if (userOpt.isEmpty()) {
            userOpt = authService.authenticateCustomer(req.getEmail(), req.getPassword());
        }

        if (userOpt.isPresent()) {
            User user = userOpt.get();
            // Trả về ID và Role để FE lưu và sử dụng cho các API Booking
            return ResponseEntity.ok(
                    Map.of(
                            "message", "Đăng nhập thành công.",
                            "id", user.getId(),
                            "role", user.getRole(),
                            "email", user.getEmail()
                    )
            );
        }

        return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(
                Map.of("message", "Email hoặc mật khẩu không đúng.")
        );
    }
}