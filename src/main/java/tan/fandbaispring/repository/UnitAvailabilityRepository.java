package tan.fandbaispring.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import tan.fandbaispring.model.UnitAvailability;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

public interface UnitAvailabilityRepository extends JpaRepository<UnitAvailability, Long> {
    List<UnitAvailability> findByTypeIdAndDateBetween(Long typeId, LocalDate start, LocalDate end);
    Optional<UnitAvailability> findByTypeIdAndDate(Long typeId, LocalDate date);
}


