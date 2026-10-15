import {existsSync} from 'node:fs';
import {Config} from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(95);
Config.setOverwriteOutput(true);

// O Smart App Control do Windows 11 barra o Chrome que o Remotion baixa ("spawn UNKNOWN"); o Edge do sistema roda.
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
if (existsSync(EDGE)) Config.setBrowserExecutable(EDGE);
