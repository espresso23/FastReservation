package tan.fandbaispring.model;

import jakarta.persistence.*;
import lombok.Data;

import java.time.LocalDate;

@Entity
@Data
public class Booking {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // --- Liên kết Cơ bản ---
    private Long userId; // End User đặt chỗ
    private String establishmentId; // FK tới Establishment
    private String partnerId; // ID của đối tác (Lấy từ Establishment.ownerId)

    // --- Chi tiết Giao dịch ---
    private LocalDate startDate; // Ngày nhận phòng/sử dụng
    private Integer duration; // Số đêm (cho Hotel) hoặc Số người (cho Restaurant)
    private Long totalPriceVnd;

    @Enumerated(EnumType.STRING)
    private BookingStatus status; // PENDING_PAYMENT, CONFIRMED, CANCELLED

    // --- Chi tiết Tồn kho (MỚI) ---
    // Các trường này ghi lại chi tiết loại phòng/bàn đã được đặt thành công

    private String bookedItemType; // VD: STANDARD_ROOM, VIP_TABLE, POOL_VIEW
    private String bookedFloorArea; // VD: Tầng 5, Khu vực ngoài trời, Bàn số 10

    // NOTE: Các trường này được gán giá trị từ FinalResultResponse/Inventory
    // khi API /confirm-payment được gọi.
}