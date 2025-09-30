package tan.fandbaispring.dto;

import lombok.Data;
import java.time.LocalDate;

@Data
public class InventoryUpdateRequest {

    private String ownerId; // ID của đối tác đang cập nhật (Cần thiết cho việc kiểm tra quyền sở hữu)
    private String establishmentId;

    private LocalDate date; // Ngày áp dụng tồn kho

    private String itemType; // Loại phòng/bàn (VD: STANDARD_ROOM, VIP_TABLE)
    private String floorArea; // Vị trí (VD: Tầng 5, Khu vực ngoài trời)

    private int totalUnits; // Tổng số đơn vị có thể bán (VD: 10 phòng)
    private Long price; // Giá/đơn vị (VD: 1,500,000 VND)

    // Ảnh minh họa và thuộc tính để lọc theo sở thích
    private String itemImageUrl;
    private Boolean hasBalcony;
}