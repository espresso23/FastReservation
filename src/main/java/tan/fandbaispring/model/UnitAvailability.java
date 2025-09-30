package tan.fandbaispring.model;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDate;

@Entity
@Data
@Table(uniqueConstraints = @UniqueConstraint(columnNames = {"typeId", "variantId", "date"}))
public class UnitAvailability {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long typeId; // FK tới UnitType
    // variantId không còn dùng trong mô hình đơn giản
    private LocalDate date;

    private Integer totalUnits;
    private Integer unitsBooked;

    private Long overridePrice; // null => dùng basePrice

    @Version
    private Long version; // Khóa lạc quan
}


