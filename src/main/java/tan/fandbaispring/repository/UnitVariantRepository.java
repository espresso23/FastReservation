package tan.fandbaispring.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import tan.fandbaispring.model.UnitVariant;

import java.util.List;

public interface UnitVariantRepository extends JpaRepository<UnitVariant, Long> {
    List<UnitVariant> findByTypeId(Long typeId);
}


