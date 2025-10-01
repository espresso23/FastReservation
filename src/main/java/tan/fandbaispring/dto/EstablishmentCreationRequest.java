package tan.fandbaispring.dto;

import lombok.Data;
import java.util.List;

@Data
public class EstablishmentCreationRequest {
    // Trường cần thiết cho Public API (FE gửi lên)
    private String ownerId; // ID của đối tác đang tạo (FE gửi lên sau khi login)
    private String name;
    private String type; // HOTEL hoặc RESTAURANT
    private String city;
    private String address;
    private Long priceRangeVnd;
    private int starRating;
    private String descriptionLong;
    private List<String> amenitiesList;

    // Cờ quan trọng cho quản lý tồn kho
    private boolean hasInventory;
    
    // Trạng thái hoạt động của cơ sở
    private boolean isAvailable;

    // Bỏ qua imageUrlMain và imageUrlsGallery vì chúng được xử lý qua Multipart/Cloudinary.
}