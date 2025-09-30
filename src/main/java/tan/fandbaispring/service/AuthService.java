package tan.fandbaispring.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import tan.fandbaispring.model.User;
import tan.fandbaispring.model.UserRole;
import tan.fandbaispring.repository.UserRepository;

import java.util.Optional;

@Service
public class AuthService {

    @Autowired
    private UserRepository userRepository;

    /**
     * Xác thực đơn thuần (không tạo token/session)
     *
     * @param email    Email đăng nhập
     * @param password Mật khẩu
     * @return Optional<User> nếu xác thực thành công và là PARTNER.
     */
    public Optional<User> authenticatePartner(String email, String password) {
        Optional<User> userOpt = userRepository.findByEmail(email);

        if (userOpt.isPresent()) {
            User user = userOpt.get();

            // 1. Kiểm tra vai trò
            if (user.getRole() != UserRole.PARTNER) {
                return Optional.empty();
            }

            // 2. Kiểm tra mật khẩu (Mô phỏng: '123456')
            if (!"123456".equals(password)) {
                return Optional.empty();
            }

            // Thành công: Trả về đối tượng User
            return Optional.of(user);
        }
        return Optional.empty();
    }

    private Optional<User> authenticate(String email, String password, UserRole requiredRole) {
        Optional<User> userOpt = userRepository.findByEmail(email);

        if (userOpt.isPresent()) {
            User user = userOpt.get();
            if (user.getRole() != requiredRole) {
                return Optional.empty();
            }
            // Mật khẩu cứng cho demo
            if (!"123456".equals(password)) {
                return Optional.empty();
            }
            return Optional.of(user);
        }
        return Optional.empty();
    }


    public Optional<User> authenticateCustomer(String email, String password) {
        return authenticate(email, password, UserRole.CUSTOMER);
    }
}