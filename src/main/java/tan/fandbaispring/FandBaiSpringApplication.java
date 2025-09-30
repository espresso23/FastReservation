package tan.fandbaispring;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.context.annotation.ComponentScan;

@SpringBootApplication(scanBasePackages = "tan.fandbaispring")
@EntityScan(basePackages = "tan.fandbaispring.model")
public class FandBaiSpringApplication {

    public static void main(String[] args) {
        SpringApplication.run(FandBaiSpringApplication.class, args);
    }

}
