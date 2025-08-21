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
import java.util.concurrent.TimeUnit;

@Component
public class AutoLoadRunner implements CommandLineRunner {
  private static final Logger log = LoggerFactory.getLogger(AutoLoadRunner.class);

  @Override
  public void run(String... args) {
    SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
    factory.setConnectTimeout((int) Duration.ofSeconds(2).toMillis());
    factory.setReadTimeout((int) Duration.ofSeconds(2).toMillis());
    RestTemplate rt = new RestTemplate(factory);

    java.util.concurrent.ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);
    scheduler.scheduleAtFixedRate(() -> safe(rt, "/hello"), 1, 3, TimeUnit.SECONDS);
    scheduler.scheduleAtFixedRate(() -> safe(rt, "/calc?x=21&y=2"), 2, 5, TimeUnit.SECONDS);
    scheduler.scheduleAtFixedRate(() -> safe(rt, "/error"), 5, 15, TimeUnit.SECONDS);
    log.info("AutoLoadRunner started - generating traffic");
  }

  private void safe(RestTemplate rt, String path) {
    try {
      String s = rt.getForObject(new URI("http://localhost:8088" + path), String.class);
      log.info("auto call {} -> {}", path, s);
    } catch (Exception e) {
      log.error("auto call {} failed: {}", path, e.toString());
    }
  }
}
