/*
  Fairy Forest Wand: M5StickS3 WiFi station.

  Set STATION, WIFI_SSID, WIFI_PASS, HUB_URL below. Flash from Arduino IDE
  (board: M5Stack > M5StickS3, M5Stack board package >= 3.2.5,
  M5Unified >= 0.2.12). Same file on every board, only STATION changes.

  Behavior mirrors the CPX firmware (firmware/code.py):
    Idle        : slow purple breathing (dark energy), station number on screen
    Wand hit    : POST /hit to the hub; hub answers heal | wrong | done
      heal      : green sparkle + rising chime, glows green HEALED_SECONDS
      wrong     : red flash + low buzz, "not yet", back to idle
      done      : rainbow + fanfare, glows DONE_SECONDS, then rearms
    Input is only blocked HIT_COOLDOWN_MS after a hit (not for the whole
    glow) because campaign steps like "wave 5 times" and boss fights need
    repeat hits at one station.
    Hub offline : behaves as "heal" (or "done" on FINAL_STATION) so the game
                  still plays with printed cards.
    Button A    : simulate a wand hit (test without the wand)

  Hardware notes (docs.m5stack.com/en/arduino/m5sticks3/ir_nec):
    IR RX is GPIO 42 and MUST use the ESP32 RMT peripheral.
    The speaker amplifier must be OFF while receiving IR, so the speaker is
    only switched on for the length of a chime.
    IR RX needs EXT 5V output enabled (M5.Power.setExtOutput).
    Serial prints raw mark/space pairs on undecodable frames; paste that
    output if the wand is heard but never decoded (timing fix).
*/
#include <M5Unified.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include "driver/rmt_rx.h"
#include "magiquest.h"

// ---- per-station config ----------------------------------------------------
static const int STATION = 1;              // <-- change per board, 1..3
static const int FINAL_STATION = 3;
static_assert(STATION >= 1 && STATION <= 3, "STATION must be 1, 2, or 3");
static const char* WIFI_SSID = "YOUR_WIFI";
static const char* WIFI_PASS = "YOUR_PASSWORD";
static const char* HUB_URL = "http://192.168.1.10:8000";  // Mac running hub/server.py
static const uint32_t HEALED_SECONDS = 30;     // how long the green glow stays (visual only)
static const uint32_t DONE_SECONDS = 60;       // rainbow glow after a chapter ends, then rearm
static const uint32_t HIT_COOLDOWN_MS = 1500;  // input ignored this long after any hit
                                               // (short: charge/boss steps need repeat waves)
static const uint32_t WRONG_COOLDOWN_MS = 800;  // was 2000: a retry right after a red
                                                // flash was being ignored (10/29 playtest)
// Liza's wand. Matched with bit tolerance so weak/short frames still count and
// room IR noise does not. 0 = accept any wand (strict 56-pair decode).
static const uint32_t KNOWN_WAND_ID = 0xAF0E4902;
// -----------------------------------------------------------------------------

static const gpio_num_t IR_RX_PIN = GPIO_NUM_42;
static const size_t RX_SYMBOLS = 128;  // 56 bits per frame; room for a repeat + junk

static rmt_channel_handle_t rx_chan = nullptr;
static rmt_symbol_word_t rx_raw[RX_SYMBOLS];
static volatile bool rx_done = false;
static volatile size_t rx_count = 0;
static rmt_receive_config_t rx_cfg;

static bool IRAM_ATTR on_rx_done(rmt_channel_handle_t, const rmt_rx_done_event_data_t* e, void*) {
    rx_count = e->num_symbols;
    rx_done = true;
    return false;
}

static void start_receive() {
    rx_done = false;
    ESP_ERROR_CHECK(rmt_receive(rx_chan, rx_raw, sizeof(rx_raw), &rx_cfg));
}

static void setup_ir() {
    rmt_rx_channel_config_t cfg = {};
    cfg.gpio_num = IR_RX_PIN;
    cfg.clk_src = RMT_CLK_SRC_DEFAULT;
    cfg.resolution_hz = 1000000;  // 1 tick = 1 us, matches magiquest.h
    cfg.mem_block_symbols = RX_SYMBOLS;
    ESP_ERROR_CHECK(rmt_new_rx_channel(&cfg, &rx_chan));
    rmt_rx_event_callbacks_t cbs = {};
    cbs.on_recv_done = on_rx_done;
    ESP_ERROR_CHECK(rmt_rx_register_event_callbacks(rx_chan, &cbs, nullptr));
    ESP_ERROR_CHECK(rmt_enable(rx_chan));
    rx_cfg.signal_range_min_ns = 1000;       // ignore <1us glitches
    rx_cfg.signal_range_max_ns = 20000000;   // 20 ms idle ends a frame
    start_receive();
}

// Convert RMT symbols to mark/space pairs. The receiver idles high and pulls
// low on carrier, so duration0 is the mark and duration1 the space.
static bool read_wand(magiquest::Hit* hit) {
    if (!rx_done) return false;
    size_t n = rx_count;
    static magiquest::Pair pairs[RX_SYMBOLS];
    for (size_t i = 0; i < n; i++) {
        pairs[i].mark = rx_raw[i].duration0;
        pairs[i].space = rx_raw[i].duration1 ? rx_raw[i].duration1 : 5000;  // 0 = end of frame
    }
    bool ok = magiquest::decode(pairs, n, hit, KNOWN_WAND_ID);
    if (ok) {
        Serial.printf("wand id=0x%08X mag=%u\n", hit->wand_id, hit->magnitude);
    } else if (n >= 20) {
        // heard something wand-sized but could not decode: dump for timing fix
        Serial.printf("undecoded frame, %u pairs:", (unsigned)n);
        for (size_t i = 0; i < n; i++) Serial.printf(" %u/%u", pairs[i].mark, pairs[i].space);
        Serial.println();
    }
    start_receive();
    return ok;
}

// ---- screen + sound ----------------------------------------------------------
static int W, H;

static uint32_t wheel(int pos) {
    pos &= 255;
    if (pos < 85) return M5.Display.color888(255 - pos * 3, pos * 3, 0);
    if (pos < 170) { pos -= 85; return M5.Display.color888(0, 255 - pos * 3, pos * 3); }
    pos -= 170;
    return M5.Display.color888(pos * 3, 0, 255 - pos * 3);
}

static void label(const char* text, uint32_t fg) {
    M5.Display.setTextColor(fg);
    M5.Display.setTextDatum(middle_center);
    M5.Display.setTextSize(3);
    M5.Display.drawString(String(STATION), W / 2, H / 2 - 20);
    M5.Display.setTextSize(1);
    M5.Display.drawString(text, W / 2, H / 2 + 30);
}

static void breathe(uint32_t ms) {
    float phase = (ms % 3000) / 3000.0f;
    float level = phase < 0.5f ? phase * 2 : (1 - phase) * 2;
    int v = 20 + (int)(90 * level);
    M5.Display.fillScreen(M5.Display.color888(v, 0, v));
    label(WiFi.isConnected() ? "waiting" : "no wifi", M5.Display.color888(200, 160, 255));
}

// Speaker amp must be off during IR RX; bracket every sound with begin/end.
static void play(const uint16_t* notes, size_t n, uint32_t ms, uint32_t gap_ms) {
    M5.Speaker.begin();
    for (size_t i = 0; i < n; i++) {
        M5.Speaker.tone(notes[i], ms);
        delay(ms + gap_ms);
    }
    M5.Speaker.end();
}

static void heal_sparkle() {
    for (int i = 0; i < 40; i++) {
        for (int k = 0; k < 30; k++)
            M5.Display.fillCircle(random(W), random(H), random(3, 9),
                                  M5.Display.color888(0, random(40, 256), random(0, 61)));
        delay(40);
    }
    static const uint16_t chime[] = {523, 659, 784, 1047};
    play(chime, 4, 120, 10);
    M5.Display.fillScreen(M5.Display.color888(0, 200, 20));
    label("healed", TFT_BLACK);
}

static void final_rainbow() {
    for (int j = 0; j < 96; j++) {
        for (int y = 0; y < H; y += 4)
            M5.Display.fillRect(0, y, W, 4, wheel(y * 256 / H + j * 8));
        delay(30);
    }
    static const uint16_t fanfare[] = {523, 523, 523, 659, 784, 1047, 784, 1047};
    play(fanfare, 8, 150, 30);
    for (int y = 0; y < H; y += 4)
        M5.Display.fillRect(0, y, W, 4, wheel(y * 256 / H));
    label("forest healed!", TFT_BLACK);
}

static void wrong_flash() {
    for (int i = 0; i < 3; i++) {
        M5.Display.fillScreen(TFT_RED);
        delay(120);
        M5.Display.fillScreen(TFT_BLACK);
        delay(80);
    }
    static const uint16_t buzz[] = {196, 147};
    play(buzz, 2, 200, 20);
    M5.Display.fillScreen(TFT_BLACK);
    label("not yet", TFT_RED);
}

// ---- hub ----------------------------------------------------------------------
// Returns "heal" | "wrong" | "done" from the hub, or "" when unreachable.
static String post_hit(uint32_t wand_id) {
    if (!WiFi.isConnected()) return "";
    HTTPClient http;
    http.setTimeout(2000);
    http.begin(String(HUB_URL) + "/hit");
    http.addHeader("Content-Type", "application/json");
    char body[64];
    snprintf(body, sizeof(body), "{\"station\": %d, \"wand_id\": \"0x%08X\"}", STATION, wand_id);
    int code = http.POST(body);
    String reply = code == 200 ? http.getString() : "";
    http.end();
    Serial.printf("hub %d %s\n", code, reply.c_str());
    // ponytail: substring match instead of a JSON parser; reply is {"result": "heal"}
    if (reply.indexOf("done") >= 0) return "done";
    if (reply.indexOf("heal") >= 0) return "heal";
    if (reply.indexOf("wrong") >= 0) return "wrong";
    return "";
}

// ---- main ------------------------------------------------------------------------
static uint32_t quiet_until = 0;  // ignore IR until this millis()
static uint32_t glow_until = 0;   // keep the last color on screen until this millis()
// No "finished" latch: the hub runs a multi-chapter campaign and station 5
// must rearm after a chapter's "done", so done is just a longer glow.

void setup() {
    auto cfg = M5.config();
    M5.begin(cfg);
    M5.Speaker.end();  // amp off: required for IR RX
    Serial.begin(115200);
    M5.Display.setRotation(0);
    W = M5.Display.width();
    H = M5.Display.height();
    M5.Display.fillScreen(TFT_BLACK);
    label("booting", TFT_WHITE);

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);  // non-blocking; status shown in breathe()

    setup_ir();
    M5.Power.setExtOutput(true, m5::ext_none);  // powers the IR receiver
}

void loop() {
    M5.update();
    uint32_t now = millis();

    magiquest::Hit hit;
    bool got = read_wand(&hit);
    if (M5.BtnA.wasPressed()) { got = true; hit.wand_id = 0; }

    if (now < quiet_until) {
        delay(30);
        return;
    }

    if (got) {
        String r = post_hit(hit.wand_id);
        if (r == "") r = (STATION == FINAL_STATION) ? "done" : "heal";  // hub offline
        if (r == "done") {
            final_rainbow();
            glow_until = millis() + DONE_SECONDS * 1000;
            quiet_until = millis() + HIT_COOLDOWN_MS;
        } else if (r == "heal") {
            heal_sparkle();
            glow_until = millis() + HEALED_SECONDS * 1000;
            quiet_until = millis() + HIT_COOLDOWN_MS;
        } else {
            wrong_flash();
            glow_until = millis() + WRONG_COOLDOWN_MS;
            quiet_until = millis() + WRONG_COOLDOWN_MS;
        }
        // drop any frames that arrived while we were busy
        if (rx_done) start_receive();
        return;
    }

    if (now < glow_until) {  // hold the last color, keep listening
        delay(30);
        return;
    }
    breathe(now);
    delay(30);
}
