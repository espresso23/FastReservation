package tan.fandbaispring.model;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDate;

@Entity
@Data
public class Inventory {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String establishmentId; // FK tới Establishment
    private LocalDate date;

    // Loại phòng/bàn (VD: STANDARD_ROOM, VIP_TABLE, POOL_VIEW)
    private String itemType;

    // Thông tin vị trí (VD: Tầng 5, Khu vực ngoài trời)
    private String floorArea;

    private int totalUnits; // Tổng số đơn vị loại này
    private int unitsBooked; // Số đơn vị đã được đặt
    private Long price; // Giá/đêm hoặc Giá/bàn

    // Ảnh minh họa cho loại phòng/bàn (nếu có)
    private String itemImageUrl;

    // Thuộc tính gợi ý cho lựa chọn người dùng
    private Boolean hasBalcony; // true: có ban công, false: không, null: không xác định
}