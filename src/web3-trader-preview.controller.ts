import * as fs from "node:fs/promises";
import { Controller, Get, HttpStatus, Param, Res } from "@nestjs/common";
import type { Response } from "express";

import { SwapHtmlFileService } from "./service/swap-html-file.service";

@Controller("web3-trader")
export class Web3TraderPreviewController {
  constructor(private readonly files: SwapHtmlFileService) {}

  /** Open the generated swap page in a browser (HTML served from disk). */
  @Get("preview/:fileId")
  async preview(@Param("fileId") fileId: string, @Res() res: Response) {
    if (!SwapHtmlFileService.isValidFileId(fileId)) {
      return res.status(HttpStatus.BAD_REQUEST).type("text/plain").send("Invalid file id");
    }
    let filePath: string;
    try {
      filePath = this.files.resolveExistingFilePath(fileId);
    } catch {
      return res
        .status(HttpStatus.SERVICE_UNAVAILABLE)
        .type("text/plain")
        .send("Swap HTML storage is not configured or path is invalid");
    }
    try {
      const html = await fs.readFile(filePath, "utf8");
      return res
        .status(HttpStatus.OK)
        .type("html")
        .set({
          "Cache-Control": "no-store, no-cache, must-revalidate",
          "Content-Security-Policy": "default-src 'self' 'unsafe-inline'; connect-src *;",
        })
        .send(html);
    } catch {
      return res.status(HttpStatus.NOT_FOUND).type("text/plain").send("Not found");
    }
  }
}
