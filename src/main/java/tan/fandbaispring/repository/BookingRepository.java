package tan.fandbaispring.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import tan.fandbaispring.model.Booking;

import java.util.List;

public interface BookingRepository extends JpaRepository<Booking, Long> {
    List<Booking> findByPartnerId(String partnerId);
    List<Booking> findByUserId(Long userId);
}