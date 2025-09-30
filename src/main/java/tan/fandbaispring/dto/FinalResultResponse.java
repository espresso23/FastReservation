package tan.fandbaispring.dto;

import lombok.Data;
import java.util.List;

/**
 * Đại diện cho một gợi ý đặt chỗ hoàn chỉnh sau khi đã qua
 * RAG Search, Price Filter, và Inventory Check.
 */
@Data
public class FinalResultResponse {

    // --- Thông tin Cơ sở (Từ Establishment Entity) ---
    private String establishmentId;
    private String establishmentName;
    private String city;
    private int starRating;

    // --- Thông tin Hình ảnh ---
    private String imageUrlMain;
    private List<String> imageUrlsGallery;

    // --- Thông tin Tồn kho/Booking (Từ Inventory Entity) ---
    // (Đây là thông tin mà người dùng chọn để tạo booking)
    private String itemType; // Loại phòng/bàn cụ thể
    private String floorArea; // Vị trí/Tầng của phòng/bàn
    private int unitsAvailable; // Số lượng còn trống hiện tại
    private Long finalPrice; // Giá cuối cùng (của loại phòng/bàn này)
    private String itemImageUrl; // Ảnh minh họa cho loại phòng/bàn

    // NOTE: Các trường này được gán từ Inventory Entity sau khi kiểm tra.
}