package tan.fandbaispring.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import tan.fandbaispring.model.User;

import java.util.Optional;

public interface UserRepository extends JpaRepository<User, Long> {

    Optional<User> findByEmail(String email);
    
}