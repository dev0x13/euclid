package net.uerrs.euclid.web;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationContext;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
public class StreamAPI {

	private final Logger log = LoggerFactory.getLogger(this.getClass());

	@Autowired
	public StreamAPI(ApplicationContext applicationContext) {
	}

	@RequestMapping(method = RequestMethod.GET, value="/ping")
	public ResponseEntity ping() {
		log.info("Ping request");
		return ResponseEntity.ok("PONG");
	}

}
