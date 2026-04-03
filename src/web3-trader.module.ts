import { Module } from "@nestjs/common";
import { ConfigModule } from "@nestjs/config";

import { SmartSwapService } from "./service/smart-swap.service";
import { SmartSwapPageService } from "./service/smart-swap-page.service";
import { SwapHtmlFileService } from "./service/swap-html-file.service";
import { SwapPageService } from "./service/swap-page.service";
import { web3TraderConfig } from "./service/web3-trader.config";
import { ZeroExService } from "./service/zeroex.service";
import { Web3TraderTools } from "./tools/web3-trader.tools";
import { Web3TraderPreviewController } from "./web3-trader-preview.controller";

@Module({
  imports: [ConfigModule.forFeature(web3TraderConfig)],
  controllers: [Web3TraderPreviewController],
  providers: [
    ZeroExService,
    SmartSwapService,
    SmartSwapPageService,
    SwapPageService,
    SwapHtmlFileService,
    Web3TraderTools,
  ],
  exports: [Web3TraderTools, ZeroExService, SwapPageService, SwapHtmlFileService, SmartSwapService],
})
export class Web3TraderModule {}
