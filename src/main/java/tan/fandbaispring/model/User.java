package tan.fandbaispring.model;

import jakarta.persistence.*;
import lombok.Data;

// ... imports
// ... imports
@Entity
@Data
@Table(name = "app_user")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String email;
    private String passwordHash;

    @Enumerated(EnumType.STRING)
    private UserRole role;

}
// ...