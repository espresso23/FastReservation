package tan.fandbaispring.model;

import jakarta.persistence.*;
import lombok.Data;
import java.util.List;

@Entity
@Data
public class UnitType {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String establishmentId; // FK tới Establishment

    @Enumerated(EnumType.STRING)
    private UnitCategory category; // ROOM | TABLE

    private String code; // DELUXE, STANDARD, VIP_TABLE
    private String name; // Tên hiển thị
    private Integer capacity; // Số người phục vụ tối đa (nếu cần)

    private Boolean hasBalcony; // dành cho ROOM; TABLE có thể bỏ qua

    private Long basePrice; // Giá cơ bản (ROOM dùng)

    private Long depositAmount; // Tiền đặt cọc (TABLE dùng)

    private Integer totalUnits; // Tổng số phòng/bàn của loại (quản lý khả dụng dựa trên Booking)

    @ElementCollection
    private List<String> imageUrls; // Ảnh minh họa cố định của loại

    private Boolean active = true;
}


