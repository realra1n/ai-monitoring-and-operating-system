package com.example.demo;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import io.micrometer.observation.Observation;
import io.micrometer.observation.ObservationRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;

@RestController
public class WebController {
  private static final Logger log = LoggerFactory.getLogger(WebController.class);
  private final ObservationRegistry registry;
  private final Counter requestCounter;
  private final Timer requestTimer;

  public WebController(ObservationRegistry registry, MeterRegistry meterRegistry) {
    this.registry = registry;
    this.requestCounter = Counter.builder("http_requests_total")
        .description("Total HTTP requests")
        .tag("service", "spring-otel-demo")
        .register(meterRegistry);
    this.requestTimer = Timer.builder("http_request_duration_seconds")
        .description("HTTP request duration")
        .tag("service", "spring-otel-demo")
        .register(meterRegistry);
  }

  @GetMapping(value = "/hello", produces = MediaType.TEXT_PLAIN_VALUE)
  public String hello() {
    return Observation.createNotStarted("hello.request", registry)
        .lowCardinalityKeyValue("endpoint", "/hello")
        .observe(() -> {
          requestCounter.increment();
          log.info("Hello endpoint called at {}", LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));
          return "Hello from Spring OTEL Demo! Time: " + System.currentTimeMillis();
        });
  }

  @GetMapping(value = "/calc", produces = MediaType.TEXT_PLAIN_VALUE)
  public String calc(@RequestParam(name = "x", defaultValue = "10") int x, 
                     @RequestParam(name = "y", defaultValue = "20") int y) {
    return Observation.createNotStarted("calc.request", registry)
        .lowCardinalityKeyValue("endpoint", "/calc")
        .observe(() -> {
          try {
            return requestTimer.recordCallable(() -> {
              try {
                // Simulate some processing time
                Thread.sleep(ThreadLocalRandom.current().nextInt(10, 100));
              } catch (InterruptedException ignored) {
                Thread.currentThread().interrupt();
              }
              int z = x * y;
              log.info("Calculation performed: {} * {} = {}", x, y, z);
              return String.format("Result: %d * %d = %d", x, y, z);
            });
          } catch (Exception e) {
            log.error("Error in calc endpoint: {}", e.getMessage());
            return "Error: " + e.getMessage();
          }
        });
  }

  @GetMapping(value = "/slow", produces = MediaType.TEXT_PLAIN_VALUE)
  public String slow() {
    return Observation.createNotStarted("slow.request", registry)
        .lowCardinalityKeyValue("endpoint", "/slow")
        .observe(() -> {
          try {
            // Simulate slow processing
            int delay = ThreadLocalRandom.current().nextInt(500, 2000);
            Thread.sleep(delay);
            log.info("Slow endpoint completed after {} ms", delay);
            return "Slow response completed after " + delay + "ms";
          } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return "Interrupted";
          }
        });
  }

  @GetMapping(value = "/users", produces = MediaType.APPLICATION_JSON_VALUE)
  public Map<String, Object> getUsers() {
    return Observation.createNotStarted("users.list", registry)
        .lowCardinalityKeyValue("endpoint", "/users")
        .observe(() -> {
          log.info("Fetching user list");
          return Map.of(
              "users", new String[]{"alice", "bob", "charlie"},
              "total", 3,
              "timestamp", System.currentTimeMillis()
          );
        });
  }

  @GetMapping(value = "/users/{id}", produces = MediaType.APPLICATION_JSON_VALUE)
  public Map<String, Object> getUser(@PathVariable String id) {
    return Observation.createNotStarted("users.get", registry)
        .lowCardinalityKeyValue("endpoint", "/users/{id}")
        .lowCardinalityKeyValue("user_id", id)
        .observe(() -> {
          log.info("Fetching user with ID: {}", id);
          
          // Simulate occasional not found
          if (ThreadLocalRandom.current().nextInt(10) == 0) {
            throw new RuntimeException("User not found: " + id);
          }
          
          return Map.of(
              "id", id,
              "name", "User " + id,
              "email", "user" + id + "@example.com",
              "created", LocalDateTime.now().minusDays(ThreadLocalRandom.current().nextInt(1, 30))
          );
        });
  }

  @GetMapping(value = "/orders", produces = MediaType.APPLICATION_JSON_VALUE) 
  public Map<String, Object> getOrders() {
    return Observation.createNotStarted("orders.list", registry)
        .lowCardinalityKeyValue("endpoint", "/orders")
        .observe(() -> {
          int orderCount = ThreadLocalRandom.current().nextInt(1, 10);
          log.info("Generating {} random orders", orderCount);
          
          String[] orders = new String[orderCount];
          for (int i = 0; i < orderCount; i++) {
            orders[i] = "order-" + ThreadLocalRandom.current().nextInt(1000, 9999);
          }
          
          return Map.of(
              "orders", orders,
              "count", orderCount,
              "total_value", ThreadLocalRandom.current().nextDouble(100.0, 10000.0)
          );
        });
  }

  @GetMapping(value = "/error", produces = MediaType.TEXT_PLAIN_VALUE)
  public String error() {
    return Observation.createNotStarted("error.request", registry)
        .lowCardinalityKeyValue("endpoint", "/error")
        .observe(() -> {
          log.warn("Simulated warning before intentional error");
          
          // Randomly choose error type
          int errorType = ThreadLocalRandom.current().nextInt(3);
          switch (errorType) {
            case 0:
              throw new RuntimeException("Simulated runtime error");
            case 1:
              throw new IllegalArgumentException("Simulated validation error");
            default:
              throw new IllegalStateException("Simulated state error");
          }
        });
  }
}
