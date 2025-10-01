package tan.fandbaispring.controller;

import com.cloudinary.Cloudinary;
import com.cloudinary.utils.ObjectUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
// ... (Các imports khác)
import tan.fandbaispring.dto.EstablishmentCreationRequest;
import tan.fandbaispring.dto.InventoryUpdateRequest;
import tan.fandbaispring.dto.LoginRequest;
import tan.fandbaispring.model.*; // Bao gồm Booking, Establishment, User, Inventory, EstablishmentType
import tan.fandbaispring.repository.*; // Bao gồm các Repository cần thiết
import tan.fandbaispring.service.AiService;
import tan.fandbaispring.model.UnitType;
import tan.fandbaispring.repository.UnitTypeRepository;
import tan.fandbaispring.service.AuthService;

import java.io.IOException;
import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/partner")
public class PartnerController {

    // ... (Các Autowired hiện tại)
    @Autowired private AuthService authService;
    @Autowired private UserRepository userRepository;
    @Autowired private EstablishmentRepository establishmentRepo;
    @Autowired private BookingRepository bookingRepo;
    @Autowired private InventoryRepository inventoryRepo; // Cần thêm InventoryRepo
    @Autowired private AiService aiService;
    @Autowired private Cloudinary cloudinary; // Autowired Cloudinary
    @Autowired private UnitTypeRepository unitTypeRepo;
    // UnitAvailability no longer used in simplified flow

    // --- Hàm Hỗ trợ Upload Cloudinary ---
    private String performUpload(MultipartFile file, String folder) throws IOException {
        @SuppressWarnings("unchecked")
        Map<String, Object> uploadResult = (Map<String, Object>) cloudinary.uploader().upload(file.getBytes(),
                ObjectUtils.asMap("folder", "fast_planner_" + folder));
        return uploadResult.get("url").toString();
    }

    // --- Hàm Upload với folder theo cơ sở ---
    private String performUploadForEstablishment(MultipartFile file, String establishmentName, String establishmentAddress, String imageType) throws IOException {
        // Tạo folder name từ tên và địa chỉ cơ sở
        String sanitizedName = sanitizeFolderName(establishmentName);
        String sanitizedAddress = sanitizeFolderName(establishmentAddress);
        String folderPath = String.format("fast_planner/establishments/%s_%s/%s", 
                sanitizedName, sanitizedAddress, imageType);
        
        @SuppressWarnings("unchecked")
        Map<String, Object> uploadResult = (Map<String, Object>) cloudinary.uploader().upload(file.getBytes(),
                ObjectUtils.asMap(
                    "folder", folderPath,
                    "public_id", generateUniqueId() // Tạo unique ID để tránh trùng lặp
                ));
        return uploadResult.get("url").toString();
    }

    // --- Hàm sanitize tên folder ---
    private String sanitizeFolderName(String name) {
        if (name == null || name.trim().isEmpty()) {
            return "unknown";
        }
        return name.trim()
                .toLowerCase()
                .replaceAll("[^a-z0-9\\s]", "") // Loại bỏ ký tự đặc biệt
                .replaceAll("\\s+", "_") // Thay thế khoảng trắng bằng underscore
                .substring(0, Math.min(20, name.length())); // Giới hạn độ dài
    }

    // --- Hàm tạo unique ID ---
    private String generateUniqueId() {
        return UUID.randomUUID().toString().replace("-", "").substring(0, 8);
    }

    // --- Hàm xóa ảnh cũ khỏi Cloudinary ---
    private void deleteOldImages(List<String> oldImageUrls) {
        if (oldImageUrls == null || oldImageUrls.isEmpty()) {
            return;
        }
        
        for (String imageUrl : oldImageUrls) {
            try {
                // Extract public_id từ URL
                String publicId = extractPublicIdFromUrl(imageUrl);
                if (publicId != null && !publicId.isEmpty()) {
                    cloudinary.uploader().destroy(publicId, ObjectUtils.emptyMap());
                }
            } catch (Exception e) {
                // Log lỗi nhưng không fail request
                System.err.println("Lỗi xóa ảnh cũ: " + e.getMessage());
            }
        }
    }

    // --- Hàm extract public_id từ Cloudinary URL ---
    private String extractPublicIdFromUrl(String imageUrl) {
        if (imageUrl == null || !imageUrl.contains("cloudinary.com")) {
            return null;
        }
        
        try {
            // URL format: https://res.cloudinary.com/cloud_name/image/upload/v1234567890/folder/subfolder/filename.jpg
            String[] parts = imageUrl.split("/upload/");
            if (parts.length > 1) {
                String pathPart = parts[1];
                // Loại bỏ version prefix nếu có
                if (pathPart.startsWith("v")) {
                    pathPart = pathPart.substring(pathPart.indexOf("/") + 1);
                }
                // Loại bỏ extension
                int lastDotIndex = pathPart.lastIndexOf(".");
                if (lastDotIndex > 0) {
                    pathPart = pathPart.substring(0, lastDotIndex);
                }
                return pathPart;
            }
        } catch (Exception e) {
            System.err.println("Lỗi extract public_id: " + e.getMessage());
        }
        return null;
    }

    // Đơn giản hóa: Upload file đơn lẻ để FE lấy URL (dùng cho ảnh UnitType/khác)
    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<?> uploadSingle(@RequestPart("file") MultipartFile file,
                                          @RequestParam(value = "folder", required = false, defaultValue = "misc") String folder) {
        try {
            String url = performUpload(file, folder);
            return ResponseEntity.ok(Map.of("url", url));
        } catch (IOException ex) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("message", "Upload thất bại: " + ex.getMessage()));
        }
    }

    // Upload ảnh cho UnitType với folder structure theo cơ sở
    @PostMapping(value = "/upload/unit-type", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<?> uploadUnitTypeImage(
            @RequestPart("file") MultipartFile file,
            @RequestParam("establishmentName") String establishmentName,
            @RequestParam("establishmentAddress") String establishmentAddress,
            @RequestParam(value = "unitTypeName", required = false, defaultValue = "unit") String unitTypeName) {
        try {
            String sanitizedUnitType = sanitizeFolderName(unitTypeName);
            String url = performUploadForEstablishment(file, establishmentName, establishmentAddress, "unit_types/" + sanitizedUnitType);
            return ResponseEntity.ok(Map.of("url", url));
        } catch (IOException ex) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("message", "Upload ảnh UnitType thất bại: " + ex.getMessage()));
        }
    }

    // --- API 1: Đăng nhập (Giữ nguyên logic kiểm tra ID) ---
    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody LoginRequest req) {
        // ... (Logic đã có)
        Optional<User> userOpt = authService.authenticatePartner(req.getEmail(), req.getPassword());
        if (userOpt.isPresent()) {
            return ResponseEntity.ok(
                    Map.of(
                            "message", "Đăng nhập thành công.",
                            "ownerId", userOpt.get().getId().toString(),
                            "email", userOpt.get().getEmail()
                    )
            );
        }
        return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(
                Map.of("message", "Email hoặc mật khẩu không đúng, hoặc không phải tài khoản đối tác.")
        );
    }

    // ----------------------------------------------------------------------
    // --- API 2: Tạo Cơ sở Mới (Tích hợp Cloudinary & Multipart) ---
    // ----------------------------------------------------------------------

    @PostMapping(value = "/establishments", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<?> createEstablishment(
            @RequestPart("data") EstablishmentCreationRequest req,
            @RequestPart("mainFile") MultipartFile mainFile,
            @RequestPart("galleryFiles") List<MultipartFile> galleryFiles)
    {
        String partnerId = req.getOwnerId(); // Vẫn lấy ID từ DTO

        // 1. Kiểm tra ID đối tác
        Optional<User> partnerOpt = userRepository.findById(Long.valueOf(partnerId));
        if (partnerOpt.isEmpty() || partnerOpt.get().getRole() != UserRole.PARTNER) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(Map.of("message", "ID đối tác không hợp lệ."));
        }

        try {
            // 2. Upload Ảnh Chính và Phụ lên Cloudinary với folder structure
            String mainImageUrl = performUploadForEstablishment(mainFile, req.getName(), req.getAddress(), "main");
            List<String> galleryUrls = galleryFiles.stream()
                    .filter(file -> !file.isEmpty())
                    .map(file -> {
                        try {
                            return performUploadForEstablishment(file, req.getName(), req.getAddress(), "gallery");
                        } catch (IOException e) {
                            throw new RuntimeException("Lỗi upload ảnh phụ: " + e.getMessage());
                        }
                    })
                    .collect(Collectors.toList());

            // 3. Tạo Entity
            Establishment newEstablishment = new Establishment();
            String generatedId = UUID.randomUUID().toString().replace("-", "").substring(0, 10);

            newEstablishment.setId(generatedId);
            newEstablishment.setOwnerId(partnerId);
            newEstablishment.setName(req.getName());
            newEstablishment.setType(tan.fandbaispring.model.EstablishmentType.valueOf(req.getType().toUpperCase()));
            newEstablishment.setCity(req.getCity());
            newEstablishment.setAddress(req.getAddress());
            // Bỏ nhập khoảng giá và số sao khi tạo. Nếu FE vẫn gửi thì cũng bỏ qua.
            newEstablishment.setDescriptionLong(req.getDescriptionLong());
            newEstablishment.setAmenitiesList(req.getAmenitiesList());

            // LƯU CÁC URL VỪA UPLOAD
            newEstablishment.setImageUrlMain(mainImageUrl);
            newEstablishment.setImageUrlsGallery(galleryUrls);

            newEstablishment.setAvailable(true); // Mặc định là có sẵn
            newEstablishment.setHasInventory(req.isHasInventory()); // Lấy từ DTO

            // Đảm bảo commit DB trước khi gọi AI để Python thấy được dữ liệu
            Establishment saved = establishmentRepo.saveAndFlush(newEstablishment);
            // Log để xác nhận amenities được lưu
            System.out.println("Saved amenities: " + saved.getAmenitiesList());

            // 4. Kích hoạt cập nhật Vector Store SAU KHI COMMIT
            aiService.indexEstablishmentAfterCommit(saved.getId());

            return ResponseEntity.status(HttpStatus.CREATED).body(saved);
        } catch (RuntimeException | IOException ex) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", "Lỗi xử lý upload hoặc tạo cơ sở: " + ex.getMessage()));
        }
    }

    // ----------------------------------------------------------------------
    // --- API 2.1: Tạo Cơ sở Mới (Không cần ảnh - JSON only) ---
    // ----------------------------------------------------------------------

    @PostMapping(value = "/establishments/simple", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<?> createEstablishmentSimple(@RequestBody EstablishmentCreationRequest req) {
        String partnerId = req.getOwnerId();

        // 1. Kiểm tra ID đối tác
        Optional<User> partnerOpt = userRepository.findById(Long.valueOf(partnerId));
        if (partnerOpt.isEmpty() || partnerOpt.get().getRole() != UserRole.PARTNER) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(Map.of("message", "ID đối tác không hợp lệ."));
        }

        try {
            // 2. Tạo Establishment mới (không có ảnh)
        Establishment newEstablishment = new Establishment();
            newEstablishment.setId(UUID.randomUUID().toString());
            newEstablishment.setOwnerId(partnerId);
            newEstablishment.setName(req.getName());
            newEstablishment.setType(EstablishmentType.valueOf(req.getType()));
            newEstablishment.setCity(req.getCity());
            newEstablishment.setAddress(req.getAddress());
            newEstablishment.setDescriptionLong(req.getDescriptionLong());
            newEstablishment.setAmenitiesList(req.getAmenitiesList());
            newEstablishment.setAvailable(req.isAvailable());
            newEstablishment.setHasInventory(req.isHasInventory());

            // Không có ảnh - để trống
            newEstablishment.setImageUrlMain(null);
            newEstablishment.setImageUrlsGallery(new ArrayList<>());

            // Lưu vào database
            Establishment saved = establishmentRepo.saveAndFlush(newEstablishment);

            // 3. Cập nhật Vector Store
            aiService.indexEstablishmentAfterCommit(saved.getId());

        return ResponseEntity.status(HttpStatus.CREATED).body(saved);
        } catch (Exception ex) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", "Lỗi tạo cơ sở: " + ex.getMessage()));
        }
    }

    // ----------------------------------------------------------------------
    // --- API 2.2: Lấy danh sách Establishments (Để mapping UnitType) ---
    // ----------------------------------------------------------------------

    @GetMapping("/establishments")
    public ResponseEntity<?> listEstablishments() {
        List<Establishment> establishments = establishmentRepo.findAll();
        return ResponseEntity.ok(establishments);
    }

    // ----------------------------------------------------------------------
    // --- API 3: Quản lý Inventory (Tồn kho) ---
    // ----------------------------------------------------------------------

    @PostMapping("/inventory")
    public ResponseEntity<?> updateInventory(@RequestBody InventoryUpdateRequest req) {

        // 1. Kiểm tra quyền (Giả định req có establishmentId)
        Optional<Establishment> estOpt = establishmentRepo.findById(req.getEstablishmentId());
        if (estOpt.isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("message", "Không tìm thấy cơ sở này."));
        }

        // (Trong thực tế, cần kiểm tra: estOpt.get().getOwnerId() == req.getOwnerId())

        // 2. Xử lý Logic Inventory: Tìm kiếm hoặc tạo mới
        Optional<Inventory> invOpt = inventoryRepo.findByEstablishmentIdAndDateAndItemType(
                req.getEstablishmentId(), req.getDate(), req.getItemType());

        Inventory inventory = invOpt.orElseGet(Inventory::new);

        // 3. Gán/Cập nhật dữ liệu
        inventory.setEstablishmentId(req.getEstablishmentId());
        inventory.setDate(req.getDate());
        inventory.setItemType(req.getItemType());
        inventory.setFloorArea(req.getFloorArea());
        inventory.setPrice(req.getPrice());
        inventory.setTotalUnits(req.getTotalUnits());
        inventory.setItemImageUrl(req.getItemImageUrl());
        inventory.setHasBalcony(req.getHasBalcony());

        // CHÚ Ý: KHÔNG bao giờ reset unitsBooked ở đây. Nó chỉ được cập nhật khi có booking.
        if (inventory.getUnitsBooked() == 0 && invOpt.isEmpty()) {
            inventory.setUnitsBooked(0);
        }

        Inventory saved = inventoryRepo.save(inventory);

        return ResponseEntity.ok(saved);
    }

    // ------------------ TYPE APIs (ROOM/TABLE chung) ------------------
    @PostMapping("/types")
    public ResponseEntity<?> createType(@RequestBody UnitType type) {
        UnitType saved = unitTypeRepo.save(type);
        return ResponseEntity.status(HttpStatus.CREATED).body(saved);
    }


    @GetMapping("/types/{establishmentId}")
    public ResponseEntity<?> listTypes(@PathVariable String establishmentId) {
        List<UnitType> types = unitTypeRepo.findByEstablishmentIdAndActiveTrue(establishmentId);
        // Trả kèm tên và địa chỉ cơ sở để FE hiển thị đẹp
        Optional<Establishment> estOpt = establishmentRepo.findById(establishmentId);
        Map<String, Object> meta;
        if (estOpt.isPresent()) {
            Establishment e = estOpt.get();
            meta = new HashMap<>();
            meta.put("establishmentName", e.getName());
            meta.put("establishmentAddress", e.getAddress());
        } else {
            meta = new HashMap<>();
        }
        Map<String, Object> body = new HashMap<>();
        body.put("items", types);
        body.put("meta", meta);
        return ResponseEntity.ok(body);
    }

    // Cập nhật UnitType
    @PutMapping("/types/{typeId}")
    public ResponseEntity<?> updateType(@PathVariable Long typeId, @RequestBody UnitType input) {
        Optional<UnitType> opt = unitTypeRepo.findById(typeId);
        if (opt.isEmpty()) return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("message", "Không tìm thấy loại"));
        UnitType t = opt.get();
        // Cho phép cập nhật các field chính
        t.setCategory(input.getCategory() != null ? input.getCategory() : t.getCategory());
        t.setCode(input.getCode() != null ? input.getCode() : t.getCode());
        t.setName(input.getName() != null ? input.getName() : t.getName());
        t.setCapacity(input.getCapacity() != null ? input.getCapacity() : t.getCapacity());
        t.setHasBalcony(input.getHasBalcony() != null ? input.getHasBalcony() : t.getHasBalcony());
        t.setBasePrice(input.getBasePrice() != null ? input.getBasePrice() : t.getBasePrice());
        t.setDepositAmount(input.getDepositAmount() != null ? input.getDepositAmount() : t.getDepositAmount());
        t.setTotalUnits(input.getTotalUnits() != null ? input.getTotalUnits() : t.getTotalUnits());
        t.setImageUrls(input.getImageUrls() != null ? input.getImageUrls() : t.getImageUrls());
        t.setActive(input.getActive() != null ? input.getActive() : t.getActive());
        UnitType saved = unitTypeRepo.save(t);
        return ResponseEntity.ok(saved);
    }

    // Xóa UnitType
    @DeleteMapping("/types/{typeId}")
    public ResponseEntity<?> deleteType(@PathVariable Long typeId) {
        Optional<UnitType> opt = unitTypeRepo.findById(typeId);
        if (opt.isEmpty()) return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("message", "Không tìm thấy loại"));
        unitTypeRepo.deleteById(typeId);
        return ResponseEntity.ok(Map.of("status", "deleted"));
    }


    // --- API 4: Xem Booking của tôi (Giữ nguyên) ---
    @GetMapping("/bookings/{ownerId}")
    public ResponseEntity<?> getMyBookings(@PathVariable String ownerId) {
        // ... (Logic đã có)
        Optional<User> partnerOpt = userRepository.findById(Long.valueOf(ownerId));
        if (partnerOpt.isEmpty() || partnerOpt.get().getRole() != UserRole.PARTNER) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(Map.of("message", "ID đối tác không hợp lệ."));
        }

        List<Booking> bookings = bookingRepo.findByPartnerId(ownerId);
        return ResponseEntity.ok(bookings);
    }

    // Cập nhật trạng thái booking (Partner)
    @PostMapping("/bookings/{bookingId}/status")
    public ResponseEntity<?> updateBookingStatus(@PathVariable Long bookingId, @RequestBody Map<String, String> body) {
        String status = body.get("status");
        Optional<Booking> opt = bookingRepo.findById(bookingId);
        if (opt.isEmpty()) return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("message","Booking không tồn tại"));
        try {
            Booking b = opt.get();
            BookingStatus oldStatus = b.getStatus();
            BookingStatus newStatus = BookingStatus.valueOf(status);

            // Điều chỉnh tồn kho nếu thay đổi giữa CONFIRMED và CANCELLED
            if (oldStatus != newStatus) {
                if (oldStatus == BookingStatus.CONFIRMED && newStatus == BookingStatus.CANCELLED) {
                    inventoryRepo.findByEstablishmentIdAndDateAndItemType(b.getEstablishmentId(), b.getStartDate(), b.getBookedItemType())
                            .ifPresent(inv -> {
                                int booked = inv.getUnitsBooked();
                                inv.setUnitsBooked(Math.max(0, booked - 1));
                                inventoryRepo.save(inv);
                            });
                }
                if (oldStatus == BookingStatus.CANCELLED && newStatus == BookingStatus.CONFIRMED) {
                    inventoryRepo.findByEstablishmentIdAndDateAndItemType(b.getEstablishmentId(), b.getStartDate(), b.getBookedItemType())
                            .ifPresent(inv -> {
                                int booked = inv.getUnitsBooked();
                                inv.setUnitsBooked(booked + 1);
                                inventoryRepo.save(inv);
                            });
                }
            }

            b.setStatus(newStatus);
            bookingRepo.save(b);
            return ResponseEntity.ok(Map.of("message","Cập nhật thành công"));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of("message","Trạng thái không hợp lệ"));
        }
    }


    // --- API 5: Xem Cơ sở của tôi (Mới) ---
    @GetMapping("/establishments/{ownerId}")
    public ResponseEntity<?> getMyEstablishments(@PathVariable String ownerId) {

        Optional<User> partnerOpt = userRepository.findById(Long.valueOf(ownerId));
        if (partnerOpt.isEmpty() || partnerOpt.get().getRole() != UserRole.PARTNER) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(Map.of("message", "ID đối tác không hợp lệ."));
        }

        List<Establishment> establishments = establishmentRepo.findByOwnerId(ownerId);
        return ResponseEntity.ok(establishments);
    }

    // --- API 6: Xem chi tiết 1 cơ sở theo ID ---
    @GetMapping("/establishment/{id}")
    public ResponseEntity<?> getEstablishmentById(@PathVariable String id) {
        return establishmentRepo.findById(id)
                .<ResponseEntity<?>>map(ResponseEntity::ok)
                .orElse(ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body(Map.of("message", "Không tìm thấy cơ sở.")));
    }

    // --- API 7: Cập nhật cơ sở ---
    @PutMapping(value = "/establishments/{id}", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<?> updateEstablishment(
            @PathVariable String id,
            @RequestPart("data") EstablishmentCreationRequest req,
            @RequestPart(value = "mainFile", required = false) MultipartFile mainFile,
            @RequestPart(value = "galleryFiles", required = false) List<MultipartFile> galleryFiles) {
        
        // 1. Kiểm tra cơ sở tồn tại và quyền sở hữu
        Optional<Establishment> establishmentOpt = establishmentRepo.findById(id);
        if (establishmentOpt.isEmpty()) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(Map.of("message", "Không tìm thấy cơ sở."));
        }
        
        Establishment establishment = establishmentOpt.get();
        
        // Kiểm tra quyền sở hữu
        if (!establishment.getOwnerId().equals(req.getOwnerId())) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(Map.of("message", "Bạn không có quyền cập nhật cơ sở này."));
        }

        try {
            // 2. Cập nhật thông tin cơ bản
            establishment.setName(req.getName());
            establishment.setType(EstablishmentType.valueOf(req.getType().toUpperCase()));
            establishment.setCity(req.getCity());
            establishment.setAddress(req.getAddress());
            establishment.setPriceRangeVnd(req.getPriceRangeVnd());
            establishment.setStarRating(req.getStarRating());
            establishment.setDescriptionLong(req.getDescriptionLong());
            establishment.setAmenitiesList(req.getAmenitiesList());
            establishment.setAvailable(req.isAvailable());
            establishment.setHasInventory(req.isHasInventory());

            // 3. Xử lý ảnh chính (nếu có)
            if (mainFile != null && !mainFile.isEmpty()) {
                // Xóa ảnh cũ trước khi upload ảnh mới
                if (establishment.getImageUrlMain() != null) {
                    deleteOldImages(List.of(establishment.getImageUrlMain()));
                }
                String mainImageUrl = performUploadForEstablishment(mainFile, req.getName(), req.getAddress(), "main");
                establishment.setImageUrlMain(mainImageUrl);
            }

            // 4. Xử lý ảnh gallery (nếu có)
            if (galleryFiles != null && !galleryFiles.isEmpty()) {
                // Xóa ảnh gallery cũ trước khi upload ảnh mới
                if (establishment.getImageUrlsGallery() != null && !establishment.getImageUrlsGallery().isEmpty()) {
                    deleteOldImages(establishment.getImageUrlsGallery());
                }
                List<String> galleryUrls = galleryFiles.stream()
                        .filter(file -> !file.isEmpty())
                        .map(file -> {
                            try {
                                return performUploadForEstablishment(file, req.getName(), req.getAddress(), "gallery");
                            } catch (IOException e) {
                                throw new RuntimeException("Lỗi upload ảnh gallery: " + e.getMessage());
                            }
                        })
                        .collect(Collectors.toList());
                establishment.setImageUrlsGallery(galleryUrls);
            }

            // 5. Lưu cơ sở đã cập nhật
            Establishment saved = establishmentRepo.save(establishment);

            // 6. Cập nhật AI Vector Store
            try {
                aiService.updateEstablishmentInVectorStore(id);
            } catch (Exception e) {
                // Log lỗi nhưng không fail request
                System.err.println("Lỗi cập nhật Vector Store: " + e.getMessage());
            }

            return ResponseEntity.ok(saved);

        } catch (IOException ex) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("message", "Lỗi upload ảnh: " + ex.getMessage()));
        } catch (Exception ex) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("message", "Lỗi cập nhật cơ sở: " + ex.getMessage()));
        }
    }

    // --- API 8: Xóa cơ sở ---
    @DeleteMapping("/establishments/{id}")
    public ResponseEntity<?> deleteEstablishment(
            @PathVariable String id,
            @RequestParam String ownerId) {
        
        // 1. Kiểm tra cơ sở tồn tại và quyền sở hữu
        Optional<Establishment> establishmentOpt = establishmentRepo.findById(id);
        if (establishmentOpt.isEmpty()) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(Map.of("message", "Không tìm thấy cơ sở."));
        }
        
        Establishment establishment = establishmentOpt.get();
        
        // Kiểm tra quyền sở hữu
        if (!establishment.getOwnerId().equals(ownerId)) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(Map.of("message", "Bạn không có quyền xóa cơ sở này."));
        }

        try {
            // 2. Kiểm tra có booking nào đang pending/confirmed không
            List<Booking> activeBookings = bookingRepo.findByEstablishmentIdAndStatusIn(
                    id, Arrays.asList(BookingStatus.PENDING_PAYMENT, BookingStatus.CONFIRMED));
            
            if (!activeBookings.isEmpty()) {
                return ResponseEntity.status(HttpStatus.CONFLICT)
                        .body(Map.of("message", "Không thể xóa cơ sở có booking đang hoạt động. " +
                                "Vui lòng hủy tất cả booking trước khi xóa cơ sở."));
            }

            // 3. Xóa tất cả ảnh khỏi Cloudinary
            List<String> allImageUrls = new ArrayList<>();
            if (establishment.getImageUrlMain() != null) {
                allImageUrls.add(establishment.getImageUrlMain());
            }
            if (establishment.getImageUrlsGallery() != null) {
                allImageUrls.addAll(establishment.getImageUrlsGallery());
            }
            
            // Xóa ảnh của UnitType
            List<UnitType> unitTypes = unitTypeRepo.findByEstablishmentId(id);
            for (UnitType unitType : unitTypes) {
                if (unitType.getImageUrls() != null) {
                    allImageUrls.addAll(unitType.getImageUrls());
                }
            }
            
            deleteOldImages(allImageUrls);

            // 4. Xóa các UnitType liên quan
            unitTypeRepo.deleteAll(unitTypes);

            // 5. Xóa các Inventory liên quan
            List<Inventory> inventories = inventoryRepo.findByEstablishmentId(id);
            inventoryRepo.deleteAll(inventories);

            // 6. Xóa cơ sở
            establishmentRepo.deleteById(id);

            // 6. Cập nhật AI Vector Store (xóa khỏi vector store)
            try {
                aiService.removeEstablishmentFromVectorStore(id);
            } catch (Exception e) {
                // Log lỗi nhưng không fail request
                System.err.println("Lỗi xóa khỏi Vector Store: " + e.getMessage());
            }

            return ResponseEntity.ok(Map.of("message", "Đã xóa cơ sở thành công."));

        } catch (Exception ex) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("message", "Lỗi xóa cơ sở: " + ex.getMessage()));
        }
    }

    // --- API 9: Cập nhật trạng thái cơ sở (Mở/Đóng) ---
    @PatchMapping("/establishments/{id}/status")
    public ResponseEntity<?> updateEstablishmentStatus(
            @PathVariable String id,
            @RequestParam String ownerId,
            @RequestParam boolean isAvailable) {
        
        // 1. Kiểm tra cơ sở tồn tại và quyền sở hữu
        Optional<Establishment> establishmentOpt = establishmentRepo.findById(id);
        if (establishmentOpt.isEmpty()) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(Map.of("message", "Không tìm thấy cơ sở."));
        }
        
        Establishment establishment = establishmentOpt.get();
        
        // Kiểm tra quyền sở hữu
        if (!establishment.getOwnerId().equals(ownerId)) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(Map.of("message", "Bạn không có quyền cập nhật cơ sở này."));
        }

        try {
            // 2. Cập nhật trạng thái
            establishment.setAvailable(isAvailable);
            establishmentRepo.save(establishment);

            // 3. Cập nhật AI Vector Store
            try {
                aiService.updateEstablishmentInVectorStore(id);
            } catch (Exception e) {
                System.err.println("Lỗi cập nhật Vector Store: " + e.getMessage());
            }

            return ResponseEntity.ok(Map.of(
                    "message", "Đã cập nhật trạng thái cơ sở thành công.",
                    "isAvailable", isAvailable
            ));

        } catch (Exception ex) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("message", "Lỗi cập nhật trạng thái: " + ex.getMessage()));
        }
    }

    // --- API 10: Lấy thống kê cơ sở ---
    @GetMapping("/establishments/{id}/stats")
    public ResponseEntity<?> getEstablishmentStats(@PathVariable String id, @RequestParam String ownerId) {
        
        // 1. Kiểm tra cơ sở tồn tại và quyền sở hữu
        Optional<Establishment> establishmentOpt = establishmentRepo.findById(id);
        if (establishmentOpt.isEmpty()) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(Map.of("message", "Không tìm thấy cơ sở."));
        }
        
        Establishment establishment = establishmentOpt.get();
        
        // Kiểm tra quyền sở hữu
        if (!establishment.getOwnerId().equals(ownerId)) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(Map.of("message", "Bạn không có quyền xem thống kê cơ sở này."));
        }

        try {
            // 2. Thống kê booking
            List<Booking> allBookings = bookingRepo.findByEstablishmentId(id);
            long totalBookings = allBookings.size();
            long confirmedBookings = allBookings.stream()
                    .filter(b -> b.getStatus() == BookingStatus.CONFIRMED)
                    .count();
            long pendingBookings = allBookings.stream()
                    .filter(b -> b.getStatus() == BookingStatus.PENDING_PAYMENT)
                    .count();
            long cancelledBookings = allBookings.stream()
                    .filter(b -> b.getStatus() == BookingStatus.CANCELLED)
                    .count();

            // 3. Thống kê UnitType
            List<UnitType> unitTypes = unitTypeRepo.findByEstablishmentId(id);
            long totalUnitTypes = unitTypes.size();
            long activeUnitTypes = unitTypes.stream()
                    .filter(UnitType::getActive)
                    .count();

            // 4. Thống kê Inventory
            List<Inventory> inventories = inventoryRepo.findByEstablishmentId(id);
            long totalInventoryItems = inventories.size();

            // 5. Doanh thu (tính từ booking confirmed)
            long totalRevenue = allBookings.stream()
                    .filter(b -> b.getStatus() == BookingStatus.CONFIRMED)
                    .mapToLong(Booking::getTotalPriceVnd)
                    .sum();

            Map<String, Object> stats = new HashMap<>();
            stats.put("establishmentId", id);
            stats.put("establishmentName", establishment.getName());
            stats.put("totalBookings", totalBookings);
            stats.put("confirmedBookings", confirmedBookings);
            stats.put("pendingBookings", pendingBookings);
            stats.put("cancelledBookings", cancelledBookings);
            stats.put("totalUnitTypes", totalUnitTypes);
            stats.put("activeUnitTypes", activeUnitTypes);
            stats.put("totalInventoryItems", totalInventoryItems);
            stats.put("totalRevenue", totalRevenue);
            stats.put("isAvailable", establishment.isAvailable());

            return ResponseEntity.ok(stats);

        } catch (Exception ex) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("message", "Lỗi lấy thống kê: " + ex.getMessage()));
        }
    }
}