import { randomBytes } from "node:crypto";
import * as fs from "node:fs/promises";
import * as path from "node:path";
import { Inject, Injectable } from "@nestjs/common";
import { ConfigType } from "@nestjs/config";

import { web3TraderConfig } from "./web3-trader.config";

/** fileId = `${Date.now()}-${16 hex}` — safe for URL and filename */
const FILE_ID_RE = /^\d+-[a-f0-9]{16}$/;

@Injectable()
export class SwapHtmlFileService {
  constructor(
    @Inject(web3TraderConfig.KEY)
    private readonly cfg: ConfigType<typeof web3TraderConfig>,
  ) {}

  assertOutputDirConfigured(): void {
    const dir = this.cfg.htmlOutputDir?.trim();
    if (!dir) {
      throw new Error("WEB3_TRADER_HTML_OUTPUT_DIR is not set — cannot persist swap HTML or build preview URLs");
    }
  }

  getOutputDir(): string {
    this.assertOutputDirConfigured();
    return path.resolve(this.cfg.htmlOutputDir.trim());
  }

  /** Reserve a new file id and preview URL (no file written yet — use for embedded hostedUrl in HTML). */
  allocatePreviewTarget(): { fileId: string; previewUrl: string } {
    this.assertOutputDirConfigured();
    const fileId = `${Date.now()}-${randomBytes(8).toString("hex")}`;
    const port = process.env.PORT || "3850";
    const base = (this.cfg.publicBaseUrl?.trim() || `http://127.0.0.1:${port}`).replace(/\/$/, "");
    const previewUrl = `${base}/web3-trader/preview/${fileId}`;
    return { fileId, previewUrl };
  }

  /** Persist HTML as `{fileId}.html` (never overwrites — fileId is unique per allocate). */
  async writeHtmlForId(fileId: string, html: string): Promise<void> {
    if (!FILE_ID_RE.test(fileId)) {
      throw new Error("Invalid file id");
    }
    const root = this.getOutputDir();
    await fs.mkdir(root, { recursive: true });
    const fullPath = path.join(root, `${fileId}.html`);
    await fs.writeFile(fullPath, html, "utf8");
  }

  resolveExistingFilePath(fileId: string): string {
    if (!FILE_ID_RE.test(fileId)) {
      throw new Error("Invalid file id");
    }
    const root = this.getOutputDir();
    const full = path.resolve(root, `${fileId}.html`);
    const relative = path.relative(root, full);
    if (relative.startsWith("..") || path.isAbsolute(relative)) {
      throw new Error("Invalid path");
    }
    return full;
  }

  static isValidFileId(fileId: string): boolean {
    return FILE_ID_RE.test(fileId);
  }
}
