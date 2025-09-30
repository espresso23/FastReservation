package tan.fandbaispring.model;

import jakarta.persistence.*;
import lombok.Data;

@Entity
@Data
public class UnitVariant {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long typeId; // FK tới UnitType

    private Integer bedCount; // số giường (2 = phòng đôi)
    private String bedType;   // DOUBLE/QUEEN/KING/TWIN...

    private Boolean hasWindow; // ví dụ: có cửa sổ
    private String view;       // SEA/MOUNTAIN/CITY

    private Long extraPriceDelta; // cộng thêm vào basePrice nếu có
}


