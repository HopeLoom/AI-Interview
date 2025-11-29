export class TTSStreamingService {
    private audioContext: AudioContext | null = null;
    private queue: Uint8Array[] = [];
    private sourceNode: AudioBufferSourceNode | null = null;
    public isPlaying = false; // Prevents overlapping playback
    private minBufferSize = 1024*16; // Minimum chunk size to prevent noise
    private isBufferPlaying = false; // Prevents overlapping buffer playback
    /**
     * Play audio from a streaming source and return a Promise when done.
     * @param audioStream The streaming source (AsyncIterable).
     * @param onComplete Callback to execute when all audio is played.
     * @param onError Callback to execute when an error occurs.
     */
    async playStreamedAudio(audioStream: AsyncIterable<Uint8Array>, onComplete?: () => void, onError?:() => void): Promise<void> {
        
        if (this.isPlaying) {
            console.warn("Already playing audio, skipping restart...");
            return;
        }
  
        this.stopAudio();
        console.log("Playing streamed audio inside TTS...");
    
        this.audioContext = new AudioContext();
    
        if (this.audioContext.state === "suspended") {
            console.log("Resuming AudioContext...");
            await this.audioContext.resume();
        }
    
        try {
            this.isPlaying = true;
    
            for await (const chunk of audioStream) {
                console.log("Received chunk inside TTS Service:", chunk.byteLength, "bytes");
                this.queue.push(chunk);
    
                const totalBuffered = this.queue.reduce((sum, c) => sum + c.length, 0);
                console.log(`Current queued buffer size: ${totalBuffered} bytes`);
    
                if (totalBuffered >= this.minBufferSize) {
                    console.log("Buffer reached threshold, decoding audio...");
                    await this.decodeAndPlay(onError);
                }
            }
    
            console.log("Done processing audio stream.");
    
            if (onComplete) {
                console.log("All audio chunks played, triggering callback.");
                onComplete();
            }
        } catch (error) {
            console.error("Error processing audio stream:", error);
            if (onError) {
                console.error("Triggering error callback.");
                onError();
            }
        } finally {
            this.isPlaying = false;
        }

        if (this.queue.length > 0) {
            console.log("Flushing final buffer...");
            await this.decodeAndPlay();
        }
        console.log("Done processing audio stream.");
    }
  
    private async decodeAndPlay(onError?:()=>void) {
        if (!this.audioContext || !this.queue.length) {
            console.warn("Skipping decode: No audio context or empty queue.");
            return;
        }

        console.log("Merging and decoding audio chunks...");

        // Merge ALL chunks, ensuring none are left behind
        const mergedBuffer = this.mergeChunks(this.queue.splice(0, this.queue.length));

        console.log(`Merged buffer size for decoding: ${mergedBuffer.byteLength} bytes`);

        try {
            const audioBuffer = await this.audioContext.decodeAudioData(mergedBuffer);
            if (!audioBuffer) {
                console.error("Failed to decode audio data!");
                return;
            }

            console.log("Decoded audioBuffer, duration:", audioBuffer.duration, "seconds");

            // Ensure smooth playback by playing in sequence
            await this.playAudioBuffer(audioBuffer);

        } catch (error) {
            console.error("Error decoding audio chunk:", error);
            if (onError) {
                console.error("Triggering error callback.");
                onError();
            }
        }
    }

    private mergeChunks(chunks: Uint8Array[]): ArrayBuffer {
        const totalLength = chunks.reduce((acc, chunk) => acc + chunk.length, 0);
        console.log("🔹 Merging", chunks.length, "chunks, total size:", totalLength, "bytes");

        const mergedArray = new Uint8Array(totalLength);
        let offset = 0;
        for (const chunk of chunks) {
            mergedArray.set(chunk, offset);
            offset += chunk.length;
        }

        console.log("Merged buffer size:", mergedArray.byteLength, "bytes");
        return mergedArray.buffer;
    }

    private async playAudioBuffer(buffer: AudioBuffer): Promise<void> {
        return new Promise<void>((resolve) => {
            if (!this.audioContext) {
                console.error("AudioContext is null, cannot play audio.");
                resolve();
                return;
            }
            console.log("Creating new buffer source node...");

            // Stop any currently playing source before starting a new one
            if (this.sourceNode) {
                console.warn("Stopping previous source to prevent overlapping audio.");
                this.sourceNode.stop();
                this.sourceNode.disconnect();
                this.sourceNode = null;
            }

            this.sourceNode = this.audioContext.createBufferSource();
            this.sourceNode.buffer = buffer;
            this.sourceNode.connect(this.audioContext.destination);

            if (buffer.duration === 0) {
                console.error("Decoded buffer has duration 0! Something is wrong.");
                resolve();
                return;
            }

            console.log("Starting audio playback, duration:", buffer.duration, "seconds");
            this.isBufferPlaying = true;
            this.sourceNode.start();

            // Ensure resolve happens after playback finishes
            const timeout = setTimeout(() => {
                console.warn("Backup resolve: Last chunk may have been skipped.");
                this.isBufferPlaying = false;
                resolve();
            }, buffer.duration * 1000 + 500); // Add 500ms buffer time

            this.sourceNode.onended = () => {
                console.log("Audio chunk finished playing.");
                clearTimeout(timeout);
                this.isBufferPlaying = false;
                resolve();
            };
        });
    }

    stopAudio() {
        if (this.sourceNode) this.sourceNode.stop();
        if (this.audioContext) this.audioContext.close();
        this.audioContext = null;
        this.sourceNode = null;
        this.queue = [];
        this.isPlaying = false;
    }
}
  
export const ttStreamingService = new TTSStreamingService();
  