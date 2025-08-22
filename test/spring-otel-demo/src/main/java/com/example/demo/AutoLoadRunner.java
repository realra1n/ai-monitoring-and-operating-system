package com.example.demo;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.net.URI;
import java.time.Duration;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.TimeUnit;

@Component
public class AutoLoadRunner implements CommandLineRunner {
  private static final Logger log = LoggerFactory.getLogger(AutoLoadRunner.class);

  @Override
  public void run(String... args) {
    SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
    factory.setConnectTimeout((int) Duration.ofSeconds(5).toMillis());
    factory.setReadTimeout((int) Duration.ofSeconds(10).toMillis());
    RestTemplate rt = new RestTemplate(factory);

    java.util.concurrent.ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(3);
    
    // Basic endpoints - frequent calls
    scheduler.scheduleAtFixedRate(() -> safe(rt, "/hello"), 2, 4, TimeUnit.SECONDS);
    scheduler.scheduleAtFixedRate(() -> safe(rt, "/calc?x=" + ThreadLocalRandom.current().nextInt(1, 100) + "&y=" + ThreadLocalRandom.current().nextInt(1, 100)), 3, 6, TimeUnit.SECONDS);
    
    // REST API endpoints - moderate frequency
    scheduler.scheduleAtFixedRate(() -> safe(rt, "/users"), 5, 8, TimeUnit.SECONDS);
    scheduler.scheduleAtFixedRate(() -> safe(rt, "/users/" + ThreadLocalRandom.current().nextInt(1, 10)), 7, 12, TimeUnit.SECONDS);
    scheduler.scheduleAtFixedRate(() -> safe(rt, "/orders"), 10, 15, TimeUnit.SECONDS);
    
    // Slow endpoint - less frequent
    scheduler.scheduleAtFixedRate(() -> safe(rt, "/slow"), 15, 30, TimeUnit.SECONDS);
    
    // Error endpoint - least frequent 
    scheduler.scheduleAtFixedRate(() -> safe(rt, "/error"), 20, 45, TimeUnit.SECONDS);
    
    // Health checks - regular monitoring
    scheduler.scheduleAtFixedRate(() -> safe(rt, "/actuator/health"), 1, 10, TimeUnit.SECONDS);
    
    log.info("AutoLoadRunner started - generating comprehensive traffic patterns");
    log.info("Traffic patterns:");
    log.info("  /hello - every 4s");
    log.info("  /calc - every 6s");
    log.info("  /users - every 8s");
    log.info("  /users/{id} - every 12s");
    log.info("  /orders - every 15s");
    log.info("  /slow - every 30s");
    log.info("  /error - every 45s");
    log.info("  /actuator/health - every 10s");
  }

  private void safe(RestTemplate rt, String path) {
    try {
      long startTime = System.currentTimeMillis();
      String response = rt.getForObject(new URI("http://localhost:8088" + path), String.class);
      long duration = System.currentTimeMillis() - startTime;
      
      // Truncate long responses for logging
      String logResponse = response != null && response.length() > 100 
          ? response.substring(0, 100) + "..." 
          : response;
          
      log.info("AUTO CALL {} -> {} ({}ms)", path, logResponse, duration);
    } catch (Exception e) {
      log.error("AUTO CALL {} failed: {}", path, e.getMessage());
    }
  }
}
