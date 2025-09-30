package tan.fandbaispring.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import tan.fandbaispring.model.UnitType;

import java.util.List;

public interface UnitTypeRepository extends JpaRepository<UnitType, Long> {
    List<UnitType> findByEstablishmentIdAndActiveTrue(String establishmentId);
}


