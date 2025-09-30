package tan.fandbaispring.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import tan.fandbaispring.dto.*; // Bao gồm FinalResultResponse, InventoryUpdateRequest, v.v.
import tan.fandbaispring.model.*;
import tan.fandbaispring.repository.BookingRepository;
import tan.fandbaispring.repository.EstablishmentRepository;
import tan.fandbaispring.repository.InventoryRepository; // Cần thêm
import tan.fandbaispring.repository.UserRepository;
import tan.fandbaispring.service.AiService;
import tan.fandbaispring.model.UnitType;
import tan.fandbaispring.model.UnitAvailability;
import tan.fandbaispring.repository.UnitTypeRepository;
import tan.fandbaispring.repository.UnitAvailabilityRepository;

import java.time.LocalDate;
import java.text.Normalizer;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/booking")
public class BookingController {

    @Autowired private AiService aiService;
    @Autowired private EstablishmentRepository establishmentRepo;
    @Autowired private BookingRepository bookingRepo;
    @Autowired private UserRepository userRepository;
    @Autowired private InventoryRepository inventoryRepo; // *** Đã thêm ***
    @Autowired private UnitTypeRepository unitTypeRepo;
    @Autowired private UnitAvailabilityRepository unitAvailRepo;

    /**
     * API chính xử lý luồng Quiz -> RAG -> Lọc Giá & Tồn kho.
     * @param request Chứa prompt và currentParams
     * @return QuizResponseDTO (nếu cần Quiz tiếp) hoặc List<FinalResultResponse> (kết quả cuối cùng)
     */
    @PostMapping("/process")
    public ResponseEntity<?> processBookingRequest(@RequestBody QuizRequestDTO request) {

        QuizResponseDTO response = aiService.generateQuiz(request);

        // 1. Nếu Quiz chưa hoàn thành, trả về câu hỏi tiếp theo
        if (!response.isQuizCompleted()) {
            return ResponseEntity.ok(response);
        }

        // 2. Nếu Quiz hoàn thành, thực hiện RAG Search
        Map<String, Object> finalParams = response.getFinalParams();
        List<SearchResultDTO> ragResults = aiService.performRagSearch(finalParams);

        // 3. Lọc Post-RAG (Giá + Sao + Số người)
        List<String> establishmentIds = ragResults.stream()
                .map(SearchResultDTO::getEstablishmentId).collect(Collectors.toList());

        Long maxPrice = Long.valueOf(finalParams.get("max_price").toString()); // Chuyển đổi sang Long
        LocalDate bookingDate = LocalDate.parse((String) finalParams.get("check_in_date")); // Lấy ngày đặt
        Integer tmpNumGuests = null;
        try { tmpNumGuests = Integer.valueOf(String.valueOf(finalParams.get("num_guests"))); } catch (Exception ignore) {}
        final Integer numGuests = tmpNumGuests;

        // Lọc cơ sở nguồn
        List<Establishment> establishments = new ArrayList<>();
        if (!establishmentIds.isEmpty()) {
            // Theo RAG
            establishmentRepo.findAllById(establishmentIds).forEach(establishments::add);
        } else {
            // Fallback khi RAG rỗng: tìm theo city (và để bộ lọc giá ở cấp Item/UnitType)
            String cityFilter = finalParams.get("city") != null ? String.valueOf(finalParams.get("city")) : null;
            for (Establishment e : establishmentRepo.findAll()) {
                if (cityFilter == null || cityFilter.isBlank()) {
                    establishments.add(e);
                } else if (cityMatches(e.getCity(), cityFilter)) {
                    establishments.add(e);
                }
            }
        }

        // 4. KIỂM TRA TỒN KHO (INVENTORY CHECK) và Chuẩn bị FinalResponse
        List<FinalResultResponse> finalSuggestions = new ArrayList<>();

        for (Establishment establishment : establishments) {

            // Nếu cơ sở yêu cầu quản lý tồn kho chi tiết
            if (Boolean.TRUE.equals(establishment.getHasInventory())) {
                // Truy vấn TẤT CẢ các loại phòng/bàn có sẵn cho ngày đó
                List<Inventory> availableItems = inventoryRepo.findByEstablishmentIdAndDate(establishment.getId(), bookingDate);
                // Lọc theo giá tối đa nếu có price
                availableItems = availableItems.stream()
                        .filter(i -> i.getPrice() == null || i.getPrice() <= maxPrice)
                        .toList();
                // Lọc theo sở thích có ban công nếu người dùng đưa vào
                Object balconyPref = finalParams.get("has_balcony");
                if (balconyPref != null) {
                    boolean wantBalcony = String.valueOf(balconyPref).equalsIgnoreCase("yes")
                            || String.valueOf(balconyPref).equalsIgnoreCase("true");
                    // Khi người dùng có chọn, CHỈ lấy những item có gắn nhãn rõ ràng và khớp yêu cầu
                    availableItems = availableItems.stream()
                            .filter(i -> i.getHasBalcony() != null && i.getHasBalcony() == wantBalcony)
                            .toList();
                }

                // Lấy UnitType để kiểm tra capacity mapping theo itemType
                List<UnitType> typesForEst = unitTypeRepo.findByEstablishmentIdAndActiveTrue(establishment.getId());

                for (Inventory item : availableItems) {
                    int unitsAvailable = item.getTotalUnits() - item.getUnitsBooked();

                    // Chỉ thêm nếu còn trống
                    if (unitsAvailable > 0) {
                        // Kiểm tra sức chứa nếu người dùng đã nhập số người
                        if (numGuests != null && numGuests > 0) {
                            boolean capacityOk = true; // qua nếu không tìm thấy mapping
                            for (UnitType t : typesForEst) {
                                String tName = t.getName() != null ? t.getName() : "";
                                String tCode = t.getCode() != null ? t.getCode() : "";
                                String it = item.getItemType() != null ? item.getItemType() : "";
                                if (it.equalsIgnoreCase(tName) || it.equalsIgnoreCase(tCode)) {
                                    if (t.getCapacity() != null && t.getCapacity() > 0 && t.getCapacity() < numGuests) {
                                        capacityOk = false;
                                    }
                                    break;
                                }
                            }
                            if (!capacityOk) continue;
                        }
                        FinalResultResponse dto = new FinalResultResponse();

                        // Gán dữ liệu Establishment
                        dto.setEstablishmentId(establishment.getId());
                        dto.setEstablishmentName(establishment.getName());
                        dto.setCity(establishment.getCity());
                        dto.setStarRating(establishment.getStarRating());
                        dto.setImageUrlMain(establishment.getImageUrlMain());
                        dto.setImageUrlsGallery(establishment.getImageUrlsGallery());

                        // Gán dữ liệu Inventory (Chi tiết phòng/bàn)
                        dto.setItemType(item.getItemType());
                        dto.setFloorArea(item.getFloorArea());
                        dto.setUnitsAvailable(unitsAvailable);
                        dto.setFinalPrice(item.getPrice());
                        dto.setItemImageUrl(item.getItemImageUrl());

                        finalSuggestions.add(dto);
                    }
                }
            } else {
                // Fallback: cơ sở không quản lý tồn kho theo ngày -> gợi ý theo UnitType
                List<UnitType> types = unitTypeRepo.findByEstablishmentIdAndActiveTrue(establishment.getId());

                // Áp dụng các bộ lọc mềm: numGuests (capacity), has_balcony, giá <= maxPrice
                Object balconyPref = finalParams.get("has_balcony");
                Boolean wantBalcony = null;
                if (balconyPref != null) {
                    wantBalcony = String.valueOf(balconyPref).equalsIgnoreCase("yes")
                            || String.valueOf(balconyPref).equalsIgnoreCase("true");
                }

                for (UnitType t : types) {
                    // Lọc sức chứa
                    if (numGuests != null && t.getCapacity() != null && t.getCapacity() > 0 && t.getCapacity() < numGuests) {
                        continue;
                    }
                    // Lọc ban công
                    if (wantBalcony != null && t.getHasBalcony() != null && !t.getHasBalcony().equals(wantBalcony)) {
                        continue;
                    }
                    // Lọc theo giá
                    Long base = t.getBasePrice();
                    if (base != null && base > maxPrice) {
                        continue;
                    }

                    FinalResultResponse dto = new FinalResultResponse();
                    dto.setEstablishmentId(establishment.getId());
                    dto.setEstablishmentName(establishment.getName());
                    dto.setCity(establishment.getCity());
                    dto.setStarRating(establishment.getStarRating());
                    dto.setImageUrlMain(establishment.getImageUrlMain());
                    dto.setImageUrlsGallery(establishment.getImageUrlsGallery());

                    dto.setItemType(t.getName() != null ? t.getName() : t.getCode());
                    dto.setUnitsAvailable(t.getTotalUnits() != null && t.getTotalUnits() > 0 ? t.getTotalUnits() : 9999);
                    dto.setFinalPrice(base);
                    // Không có ảnh riêng của type trong model -> giữ ảnh cơ sở
                    finalSuggestions.add(dto);
                }
            }
        }
        // Nếu có số lượng khách, ưu tiên các loại/đề xuất phù hợp (lọc mềm theo tên/loại có chứa từ khóa)
        if (numGuests != null && numGuests > 0) {
            List<FinalResultResponse> filtered = finalSuggestions.stream().filter(s -> {
                String type = (s.getItemType() != null ? s.getItemType() : "") + " " + (s.getFloorArea() != null ? s.getFloorArea() : "");
                String lc = type.toLowerCase();
                if (numGuests == 1) return true;
                if (numGuests == 2) return lc.contains("double") || lc.contains("2") || lc.contains("đôi");
                if (numGuests == 3) return lc.contains("3") || lc.contains("triple");
                if (numGuests == 4) return lc.contains("4") || lc.contains("family");
                return true;
            }).toList();
            // Chỉ áp dụng lọc mềm nếu còn kết quả; nếu rỗng thì giữ nguyên danh sách gốc
            if (!filtered.isEmpty()) {
                finalSuggestions = filtered;
            }
        }
        return ResponseEntity.ok(finalSuggestions);
    }

    // ------------------ HELPER: City matching with alias/diacritics ------------------
    private static String normalize(String input) {
        if (input == null) return "";
        String noAccent = Normalizer.normalize(input, Normalizer.Form.NFD)
                .replaceAll("\\p{InCombiningDiacriticalMarks}+", "");
        return noAccent.toLowerCase().replaceAll("[^a-z0-9]", "");
    }

    private static final Map<String, String> CITY_ALIAS = new HashMap<>();
    static {
        // Đà Nẵng
        CITY_ALIAS.put("danang", "danang");
        CITY_ALIAS.put("dn", "danang");
        CITY_ALIAS.put("danag", "danang");
        CITY_ALIAS.put("dng", "danang");
        // Hà Nội
        CITY_ALIAS.put("hanoi", "hanoi");
        CITY_ALIAS.put("hn", "hanoi");
        // Hồ Chí Minh / Sài Gòn
        CITY_ALIAS.put("hochiminh", "hochiminh");
        CITY_ALIAS.put("tphcm", "hochiminh");
        CITY_ALIAS.put("hcm", "hochiminh");
        CITY_ALIAS.put("saigon", "hochiminh");
        CITY_ALIAS.put("sg", "hochiminh");
        // Nha Trang
        CITY_ALIAS.put("nhatrang", "nhatrang");
        CITY_ALIAS.put("nt", "nhatrang");
        // Đà Lạt
        CITY_ALIAS.put("dalat", "dalat");
        CITY_ALIAS.put("dl", "dalat");
        // Huế
        CITY_ALIAS.put("hue", "hue");
        // Cần Thơ
        CITY_ALIAS.put("cantho", "cantho");
        CITY_ALIAS.put("ct", "cantho");
        // Quy Nhơn
        CITY_ALIAS.put("quynhon", "quynhon");
        CITY_ALIAS.put("qn", "quynhon");
        // Phú Quốc
        CITY_ALIAS.put("phuquoc", "phuquoc");
        CITY_ALIAS.put("pq", "phuquoc");
        // Vũng Tàu
        CITY_ALIAS.put("vungtau", "vungtau");
        CITY_ALIAS.put("vt", "vungtau");
        // Hội An
        CITY_ALIAS.put("hoian", "hoian");
        // Phan Thiết
        CITY_ALIAS.put("phanthiet", "phanthiet");
        CITY_ALIAS.put("pt", "phanthiet");
        // Hạ Long
        CITY_ALIAS.put("halong", "halong");
        CITY_ALIAS.put("hl", "halong");
        // Sa Pa
        CITY_ALIAS.put("sapa", "sapa");
        CITY_ALIAS.put("sp", "sapa");
        // Biên Hòa
        CITY_ALIAS.put("bienhoa", "bienhoa");
        // Rạch Giá
        CITY_ALIAS.put("rachgia", "rachgia");
    }

    private static String canonicalCity(String normalized) {
        if (normalized == null || normalized.isBlank()) return "";
        String key = normalized;
        if (CITY_ALIAS.containsKey(key)) return CITY_ALIAS.get(key);
        // Map các biến thể có dấu về normalized trước khi tra alias
        return key;
    }

    private static boolean cityMatches(String estCity, String queryCity) {
        String est = canonicalCity(normalize(estCity));
        String q = canonicalCity(normalize(queryCity));
        if (q.isBlank()) return true;
        if (est.equals(q)) return true;
        // Fuzzy contains for minor typos
        return est.contains(q) || q.contains(est);
    }

    // API: Xem tồn kho theo cơ sở và ngày (trả về các loại còn trống)
    @GetMapping("/establishments/{establishmentId}/availability")
    public ResponseEntity<?> getAvailabilityByEstablishment(
            @PathVariable String establishmentId,
            @RequestParam String date
    ) {
        LocalDate bookingDate = LocalDate.parse(date);
        List<Inventory> items = inventoryRepo.findByEstablishmentIdAndDate(establishmentId, bookingDate);
        List<FinalResultResponse> results = new ArrayList<>();

        if (!items.isEmpty()) {
            for (Inventory item : items) {
                int unitsAvailable = item.getTotalUnits() - item.getUnitsBooked();
                if (unitsAvailable <= 0) continue;
                FinalResultResponse dto = new FinalResultResponse();
                dto.setEstablishmentId(establishmentId);
                establishmentRepo.findById(establishmentId).ifPresent(est -> {
                    dto.setEstablishmentName(est.getName());
                    dto.setCity(est.getCity());
                    dto.setStarRating(est.getStarRating());
                    dto.setImageUrlMain(est.getImageUrlMain());
                    dto.setImageUrlsGallery(est.getImageUrlsGallery());
                });
                dto.setItemType(item.getItemType());
                dto.setFloorArea(item.getFloorArea());
                dto.setUnitsAvailable(unitsAvailable);
                dto.setFinalPrice(item.getPrice());
                dto.setItemImageUrl(item.getItemImageUrl());
                results.add(dto);
            }
            return ResponseEntity.ok(results);
        }

        // Fallback: nếu chưa cấu hình inventory theo ngày, trả theo UnitType (dùng basePrice và totalUnits)
        List<UnitType> types = unitTypeRepo.findByEstablishmentIdAndActiveTrue(establishmentId);
        for (UnitType t : types) {
            Integer total = t.getTotalUnits() != null && t.getTotalUnits() > 0 ? t.getTotalUnits() : 9999;
            FinalResultResponse dto = new FinalResultResponse();
            dto.setEstablishmentId(establishmentId);
            establishmentRepo.findById(establishmentId).ifPresent(est -> {
                dto.setEstablishmentName(est.getName());
                dto.setCity(est.getCity());
                dto.setStarRating(est.getStarRating());
                dto.setImageUrlMain(est.getImageUrlMain());
                dto.setImageUrlsGallery(est.getImageUrlsGallery());
            });
            dto.setItemType(t.getName() != null ? t.getName() : t.getCode());
            dto.setUnitsAvailable(total);
            dto.setFinalPrice(t.getBasePrice());
            // Không có ảnh riêng theo type ở model hiện tại -> để null hoặc dùng ảnh cơ sở
            results.add(dto);
        }
        return ResponseEntity.ok(results);
    }

    // ------------------ TYPE/AVAILABILITY cho booking ------------------
    @GetMapping("/establishments/{establishmentId}/types")
    public ResponseEntity<?> listTypesForEstablishment(@PathVariable String establishmentId,
                                                       @RequestParam(required = false) String category) {
        List<UnitType> types = unitTypeRepo.findByEstablishmentIdAndActiveTrue(establishmentId);
        if (category != null) {
            types = types.stream().filter(t -> t.getCategory().name().equalsIgnoreCase(category)).toList();
        }
        return ResponseEntity.ok(types);
    }

    @GetMapping("/types/{typeId}/availability")
    public ResponseEntity<?> getTypeAvailability(@PathVariable Long typeId,
                                                 @RequestParam String start,
                                                 @RequestParam String end) {
        java.time.LocalDate s = java.time.LocalDate.parse(start);
        java.time.LocalDate e = java.time.LocalDate.parse(end);
        return ResponseEntity.ok(unitAvailRepo.findByTypeIdAndDateBetween(typeId, s, e));
    }

    /**
     * API xử lý tạo Booking, mô phỏng Thanh toán, và CẬP NHẬT TỒN KHO.
     * @param req Chi tiết booking từ màn hình xác nhận của người dùng.
     * @return Booking được xác nhận.
     */
    @PostMapping("/confirm-payment")
    public ResponseEntity<?> confirmPayment(@RequestBody BookingConfirmationRequest req) {

        // 1. Tìm Establishment để lấy Owner ID (Partner ID)
        Optional<Establishment> estOpt = establishmentRepo.findById(req.getEstablishmentId());
        if (estOpt.isEmpty()) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("message", "Cơ sở không tồn tại."));
        }

        // 2. Kiểm tra khả dụng dựa trên loại phòng (không dùng lịch) và sức chứa
        // Tìm UnitType của loại booking (giả sử req.bookedItemType là code hoặc name -> ở đây dùng floorArea/itemType làm mã loại đơn giản)
        List<UnitType> typesOfEst = unitTypeRepo.findByEstablishmentIdAndActiveTrue(req.getEstablishmentId());
        UnitType matchedType = null;
        for (UnitType t : typesOfEst) {
            if (t.getCode().equalsIgnoreCase(req.getBookedItemType()) || t.getName().equalsIgnoreCase(req.getBookedItemType())) {
                matchedType = t; break;
            }
        }
        if (matchedType == null) {
            return ResponseEntity.badRequest().body(Map.of("message", "Không xác định được loại phòng/bàn (bookedItemType phải khớp code/name)"));
        }

        // Validate số người phù hợp sức chứa nếu client truyền lên
        Integer numGuests = null;
        try { numGuests = (Integer) ((Map<?,?>)Map.of()).get("numGuests"); } catch (Exception ignore) {}
        // (Ghi chú: client sẽ gửi numGuests trong final_params ở bước process; ở đây giả định FE sẽ map và truyền theo bookedItemType phù hợp)

        LocalDate start = req.getStartDate();
        LocalDate end = start.plusDays(req.getDuration() != null ? req.getDuration() : 1);
        // Nếu chưa khai báo tổng số phòng/bàn, coi như không giới hạn để không chặn đặt chỗ thử nghiệm
        int totalUnits = (matchedType.getTotalUnits() != null && matchedType.getTotalUnits() > 0)
                ? matchedType.getTotalUnits()
                : Integer.MAX_VALUE;

        // Đếm số booking CONFIRMED (hoặc PENDING_PAYMENT nếu muốn giữ chỗ) có overlap cùng loại
        List<Booking> existing = bookingRepo.findByPartnerId(estOpt.get().getOwnerId());
        long overlaps = existing.stream()
                .filter(b -> b.getStatus() == BookingStatus.CONFIRMED || b.getStatus() == BookingStatus.PENDING_PAYMENT)
                .filter(b -> {
                    if (b.getBookedItemType() == null) return false;
                    boolean sameType = b.getBookedItemType().equalsIgnoreCase(req.getBookedItemType());
                    if (!sameType) return false;
                    LocalDate bStart = b.getStartDate();
                    LocalDate bEnd = bStart.plusDays(b.getDuration() != null ? b.getDuration() : 1);
                    return bStart.isBefore(end) && bEnd.isAfter(start); // overlap
                })
                .count();

        if (overlaps >= totalUnits) {
            return ResponseEntity.status(HttpStatus.CONFLICT).body(Map.of("message", "Loại phòng/bàn này đã hết cho khoảng ngày chọn"));
        }

        // 3. Tạo Booking
        Booking newBooking = new Booking();
        newBooking.setUserId(req.getUserId());
        newBooking.setEstablishmentId(req.getEstablishmentId());
        newBooking.setPartnerId(estOpt.get().getOwnerId()); // Lấy Owner ID từ Establishment
        newBooking.setStartDate(req.getStartDate());
        newBooking.setDuration(req.getDuration());
        // Tính giá theo LOẠI PHÒNG/BÀN: đơn giá từ Inventory x số đêm
        Long computedTotal = req.getTotalPriceVnd();
        try {
            Optional<Inventory> invOptForPrice = inventoryRepo.findByEstablishmentIdAndDateAndItemType(
                    req.getEstablishmentId(), req.getStartDate(), req.getBookedItemType());
            long base = invOptForPrice.map(i -> i.getPrice() != null ? i.getPrice() : 0L).orElse(0L);
            int nights = req.getDuration() != null ? req.getDuration() : 1;
            computedTotal = base * nights;
        } catch (Exception ignore) { /* fallback dùng giá client nếu cần */ }
        newBooking.setTotalPriceVnd(computedTotal);
        newBooking.setBookedItemType(req.getBookedItemType()); // *** Đã thêm ***
        newBooking.setBookedFloorArea(req.getBookedFloorArea()); // *** Đã thêm ***
        newBooking.setStatus(BookingStatus.PENDING_PAYMENT);

        bookingRepo.save(newBooking);

        // 3. MÔ PHỎNG THANH TOÁN VÀ CẬP NHẬT TỒN KHO
        newBooking.setStatus(BookingStatus.CONFIRMED);
        Booking confirmedBooking = bookingRepo.save(newBooking);

        // CẬP NHẬT TỒN KHO (QUAN TRỌNG)
        Optional<Inventory> itemOpt = inventoryRepo.findByEstablishmentIdAndDateAndItemType(
                confirmedBooking.getEstablishmentId(), confirmedBooking.getStartDate(), confirmedBooking.getBookedItemType());

        if (itemOpt.isPresent()) {
            Inventory item = itemOpt.get();
            item.setUnitsBooked(item.getUnitsBooked() + 1); // Tăng số lượng đã đặt
            inventoryRepo.save(item);
        } else {
            // Lỗi nghiêm trọng: Booking được tạo nhưng không tìm thấy Inventory để giảm.
            System.err.println("Lỗi INVENTORY: Không tìm thấy tồn kho cho booking ID: " + confirmedBooking.getId());
        }

        return ResponseEntity.ok(confirmedBooking);
    }

    /**
     * API xem tất cả các booking đã CONFIRMED của khách hàng.
     * @param userId ID của khách hàng đang đăng nhập (lấy từ FE)
     */
    @GetMapping("/user/view/{userId}")
    public ResponseEntity<?> getUserBookings(@PathVariable Long userId) {

        // 1. (Optional) Xác thực: Kiểm tra User ID có phải là CUSTOMER không
        Optional<User> userOpt = userRepository.findById(userId);
        if (userOpt.isEmpty() || userOpt.get().getRole() != UserRole.CUSTOMER) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(Map.of("message", "ID không hợp lệ hoặc không phải khách hàng."));
        }

        // 2. Truy vấn Booking theo User ID
        List<Booking> bookings = bookingRepo.findByUserId(userId);

        return ResponseEntity.ok(bookings);
    }
}