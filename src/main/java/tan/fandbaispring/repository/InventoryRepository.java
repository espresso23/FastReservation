package tan.fandbaispring.repository;

import tan.fandbaispring.model.Inventory;
import org.springframework.data.jpa.repository.JpaRepository;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

public interface InventoryRepository extends JpaRepository<Inventory, Long> {

    /**
     * Tìm kiếm tồn kho cho một cơ sở và một ngày cụ thể.
     * Dùng để kiểm tra TẤT CẢ các loại phòng/bàn có sẵn.
     */
    List<Inventory> findByEstablishmentIdAndDate(String establishmentId, LocalDate date);

    /**
     * Tìm kiếm tồn kho cho một loại phòng/bàn cụ thể.
     * Dùng khi xác nhận booking để cập nhật unitsBooked.
     */
    Optional<Inventory> findByEstablishmentIdAndDateAndItemType(
            String establishmentId,
            LocalDate date,
            String itemType
    );

    /**
     * Tìm tất cả inventory của một cơ sở.
     */
    List<Inventory> findByEstablishmentId(String establishmentId);
}