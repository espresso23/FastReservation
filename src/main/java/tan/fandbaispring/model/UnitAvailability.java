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
    private Long variantId; // FK tới UnitVariant (nullable với loại không có biến thể)
    private LocalDate date;

    private Integer totalUnits;
    private Integer unitsBooked;

    private Long overridePrice; // null => dùng basePrice

    @Version
    private Long version; // Khóa lạc quan
}


