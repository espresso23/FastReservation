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
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
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

        if (ragResults.isEmpty()) {
            return ResponseEntity.ok(Map.of("message", "Không tìm thấy kết quả phù hợp qua AI search."));
        }

        // 3. Lọc Post-RAG (Giá + Sao)
        List<String> establishmentIds = ragResults.stream()
                .map(SearchResultDTO::getEstablishmentId).collect(Collectors.toList());

        Long maxPrice = Long.valueOf(finalParams.get("max_price").toString()); // Chuyển đổi sang Long
        LocalDate bookingDate = LocalDate.parse((String) finalParams.get("check_in_date")); // Lấy ngày đặt

        // Lọc cơ sở theo ID từ RAG và theo giá tối đa
        List<Establishment> establishments = establishmentRepo.findByIdInAndPriceRangeVndLessThanEqual(
                establishmentIds, maxPrice
        );

        // 4. KIỂM TRA TỒN KHO (INVENTORY CHECK) và Chuẩn bị FinalResponse
        List<FinalResultResponse> finalSuggestions = new ArrayList<>();

        for (Establishment establishment : establishments) {

            // Nếu cơ sở yêu cầu quản lý tồn kho chi tiết
            if (Boolean.TRUE.equals(establishment.getHasInventory())) {
                // Truy vấn TẤT CẢ các loại phòng/bàn có sẵn cho ngày đó
                List<Inventory> availableItems = inventoryRepo.findByEstablishmentIdAndDate(establishment.getId(), bookingDate);
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

                for (Inventory item : availableItems) {
                    int unitsAvailable = item.getTotalUnits() - item.getUnitsBooked();

                    // Chỉ thêm nếu còn trống
                    if (unitsAvailable > 0) {
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
                // Nếu không quản lý tồn kho, bỏ qua để tránh trả thiếu thông tin chi tiết
            }
        }

        return ResponseEntity.ok(finalSuggestions);
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

        // 2. Tạo Booking
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