package tan.fandbaispring.dto;

import lombok.Data;
import java.time.LocalDate;

@Data
public class BookingConfirmationRequest {

    // --- Các trường đã có ---
    private Long userId;
    private String establishmentId;
    private LocalDate startDate;
    private Integer duration;
    private Long totalPriceVnd;

    // --- Các trường CẦN THIẾT cho Inventory/Booking (MỚI) ---
    private String bookedItemType;    // Tên loại phòng/bàn đã chọn
    private String bookedFloorArea;   // Vị trí/Tầng đã chọn

    // Số lượng khách để kiểm tra sức chứa loại phòng/bàn
    private Integer numGuests;
}