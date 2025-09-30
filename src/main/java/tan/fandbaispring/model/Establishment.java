package tan.fandbaispring.model;

import jakarta.persistence.*;
import lombok.Data;

import java.util.List;

@Entity
@Data
public class Establishment {

    @Id
    private String id; // Ví dụ: HTL-DN-001 hoặc RES-HN-005

    private String name;
    private String ownerId; // FK tới user.id (Đối tác sở hữu)

    @Enumerated(EnumType.STRING)
    private EstablishmentType type; // HOTEL hoặc RESTAURANT

    private String city;
    private String address;
    private Long priceRangeVnd; // Giá trung bình hoặc giá khởi điểm
    private int starRating;

    // --- Tính năng RAG/Context ---
    @Column(columnDefinition = "TEXT")
    private String descriptionLong; // Mô tả chi tiết (Nguồn dữ liệu chính cho RAG)

    @ElementCollection(fetch = FetchType.EAGER)
    @CollectionTable(name = "establishment_amenities_list", joinColumns = @JoinColumn(name = "establishment_id"))
    @Column(name = "amenities_list")
    private List<String> amenitiesList; // Danh sách tiện ích

    // --- Tính năng Hình ảnh (Cloudinary) ---
    private String imageUrlMain; // URL ảnh chính (cho Card)

    @ElementCollection
    @CollectionTable(name = "establishment_gallery", joinColumns = @JoinColumn(name = "establishment_id"))
    @Column(name = "image_url")
    private List<String> imageUrlsGallery; // URL các ảnh phụ (Gallery)

    // --- Tính năng Inventory/Booking ---
    private boolean isAvailable; // Cờ trạng thái hoạt động (Mở/Đóng)

    @Column(name = "has_inventory")
    private Boolean hasInventory; // Cờ báo hiệu cần kiểm tra tồn kho chi tiết (Inventory Table)

    @PrePersist
    private void prePersistDefaults() {
        if (hasInventory == null) {
            hasInventory = Boolean.FALSE;
        }
    }
}