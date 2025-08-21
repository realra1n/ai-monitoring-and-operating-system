package com.example.demo;

import io.micrometer.observation.Observation;
import io.micrometer.observation.ObservationRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;

import java.util.concurrent.ThreadLocalRandom;

@RestController
public class WebController {
  private static final Logger log = LoggerFactory.getLogger(WebController.class);
  private final ObservationRegistry registry;

  public WebController(ObservationRegistry registry) {
    this.registry = registry;
  }

  @GetMapping(value = "/hello", produces = MediaType.TEXT_PLAIN_VALUE)
  public String hello() {
    return Observation.createNotStarted("hello.request", registry)
        .lowCardinalityKeyValue("endpoint", "/hello")
        .observe(() -> {
          log.info("hello called");
          return "hello " + System.currentTimeMillis();
        });
  }

  @GetMapping(value = "/calc", produces = MediaType.TEXT_PLAIN_VALUE)
  public String calc(@RequestParam(name = "x") int x, @RequestParam(name = "y") int y) {
    return Observation.createNotStarted("calc.request", registry)
        .lowCardinalityKeyValue("endpoint", "/calc")
        .observe(() -> {
          try {
            Thread.sleep(ThreadLocalRandom.current().nextInt(10, 100));
          } catch (InterruptedException ignored) {}
          int z = x * y;
          log.info("calc {} * {} = {}", x, y, z);
          return String.valueOf(z);
        });
  }

  @GetMapping(value = "/error", produces = MediaType.TEXT_PLAIN_VALUE)
  public String error() {
    return Observation.createNotStarted("error.request", registry)
        .lowCardinalityKeyValue("endpoint", "/error")
        .observe(() -> {
          log.warn("simulated warning before error");
          throw new RuntimeException("simulated error");
        });
  }
}
