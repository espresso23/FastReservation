package tan.fandbaispring.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import tan.fandbaispring.model.Establishment;

import java.util.Collection;
import java.util.List;

public interface EstablishmentRepository extends JpaRepository<Establishment, String> {
    List<Establishment> findByOwnerId(String ownerId); // NEW

    List<Establishment> findByIdInAndPriceRangeVndLessThanEqual(Collection<String> id, Long priceRangeVnd);
}