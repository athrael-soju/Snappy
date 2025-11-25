/**
 * Centralized logging utility for Snappy frontend
 * 
 * Features:
 * - Environment-aware (development vs production)
 * - Structured logging with metadata
 * - Type-safe with full TypeScript support
 * - Zero dependencies
 * - Easy to extend with monitoring services (Sentry, LogRocket, etc.)
 * 
 * Usage:
 * ```typescript
 * import { logger } from '@/lib/utils/logger';
 * 
 * logger.info('User uploaded document', { fileCount: 3, totalSize: 1024 });
 * logger.error('API call failed', { error, endpoint: '/search' });
 * logger.debug('Component mounted', { componentName: 'SearchPage' });
 * ```
 */

/**
 * Log levels in order of severity
 */
export enum LogLevel {
    DEBUG = 0,
    INFO = 1,
    WARN = 2,
    ERROR = 3,
}

/**
 * Metadata that can be attached to any log entry
 */
export interface LogMetadata {
    [key: string]: unknown;
    error?: Error | unknown;
    component?: string;
    action?: string;
    userId?: string;
    requestId?: string;
    duration?: number;
}

/**
 * Structured log entry
 */
interface LogEntry {
    timestamp: string;
    level: LogLevel;
    levelName: string;
    message: string;
    metadata?: LogMetadata;
    environment: string;
}

/**
 * Logger configuration
 */
interface LoggerConfig {
    /**
     * Minimum log level to output (logs below this level are suppressed)
     */
    minLevel: LogLevel;

    /**
     * Enable console output
     */
    enableConsole: boolean;

    /**
     * Enable structured JSON output (useful for log aggregation)
     */
    enableStructured: boolean;

    /**
     * Remote logging handler (e.g., for Sentry, LogRocket, custom API)
     */
    remoteHandler?: (entry: LogEntry) => void;

    /**
     * Include stack traces for errors
     */
    includeStackTraces: boolean;
}

/**
 * Default configuration based on environment
 */
const getDefaultConfig = (): LoggerConfig => {
    const isDevelopment = process.env.NODE_ENV === 'development';

    return {
        minLevel: isDevelopment ? LogLevel.DEBUG : LogLevel.WARN,
        enableConsole: true,
        enableStructured: !isDevelopment,
        includeStackTraces: isDevelopment,
    };
};

/**
 * Logger class
 */
class Logger {
    private config: LoggerConfig;

    constructor(config?: Partial<LoggerConfig>) {
        this.config = { ...getDefaultConfig(), ...config };
    }

    /**
     * Update logger configuration at runtime
     */
    configure(config: Partial<LoggerConfig>): void {
        this.config = { ...this.config, ...config };
    }

    /**
     * Get current configuration
     */
    getConfig(): Readonly<LoggerConfig> {
        return { ...this.config };
    }

    /**
     * Create a child logger with additional context
     */
    child(context: LogMetadata): Logger {
        const childLogger = new Logger(this.config);
        const originalLog = childLogger.log.bind(childLogger);

        childLogger.log = (level: LogLevel, message: string, metadata?: LogMetadata) => {
            originalLog(level, message, { ...context, ...metadata });
        };

        return childLogger;
    }

    /**
     * Core logging method
     */
    private log(level: LogLevel, message: string, metadata?: LogMetadata): void {
        // Suppress logs below minimum level
        if (level < this.config.minLevel) {
            return;
        }

        const entry: LogEntry = {
            timestamp: new Date().toISOString(),
            level,
            levelName: LogLevel[level],
            message,
            metadata,
            environment: process.env.NODE_ENV || 'unknown',
        };

        // Console output
        if (this.config.enableConsole) {
            this.outputToConsole(entry);
        }

        // Remote handler (e.g., Sentry, custom API)
        if (this.config.remoteHandler && level >= LogLevel.ERROR) {
            try {
                this.config.remoteHandler(entry);
            } catch (error) {
                console.error('Remote logging handler failed:', error);
            }
        }
    }

    /**
     * Serialize error objects for JSON output
     */
    private serializeError(error: unknown): any {
        if (error instanceof Error) {
            return {
                ...error, // Include any custom properties first
                name: error.name,
                message: error.message,
                stack: this.config.includeStackTraces ? error.stack : undefined,
            };
        }
        return error;
    }

    /**
     * Serialize metadata for JSON output, handling Error objects
     */
    private serializeMetadata(metadata?: LogMetadata): any {
        if (!metadata) return undefined;

        const serialized: any = {};
        for (const [key, value] of Object.entries(metadata)) {
            if (value instanceof Error) {
                serialized[key] = this.serializeError(value);
            } else if (typeof value === 'object' && value !== null && 'error' in value) {
                // Handle nested error objects (e.g., ApiError with nested errors)
                serialized[key] = { ...value, error: this.serializeError((value as any).error) };
            } else {
                serialized[key] = value;
            }
        }
        return serialized;
    }

    /**
     * Output log entry to console with appropriate formatting
     */
    private outputToConsole(entry: LogEntry): void {
        const { levelName, message, metadata } = entry;

        if (this.config.enableStructured) {
            // Structured JSON output for production/log aggregation
            const serializedEntry = {
                ...entry,
                metadata: this.serializeMetadata(metadata),
            };
            console.log(JSON.stringify(serializedEntry));
            return;
        }

        // Development-friendly formatted output
        const timestamp = new Date(entry.timestamp).toLocaleTimeString();
        const prefix = `[${timestamp}] ${levelName}:`;

        // Choose appropriate console method
        const consoleMethod = this.getConsoleMethod(entry.level);

        if (metadata) {
            // Extract error for better formatting
            const { error, ...otherMetadata } = metadata;

            // Log message with metadata
            if (Object.keys(otherMetadata).length > 0) {
                consoleMethod(prefix, message, otherMetadata);
            } else {
                consoleMethod(prefix, message);
            }

            // Log error separately with stack trace if available
            if (error) {
                if (error instanceof Error && this.config.includeStackTraces) {
                    consoleMethod('Error:', error);
                } else {
                    consoleMethod('Error:', error);
                }
            }
        } else {
            consoleMethod(prefix, message);
        }
    }

    /**
     * Get appropriate console method for log level
     */
    private getConsoleMethod(level: LogLevel): Console['log'] {
        switch (level) {
            case LogLevel.DEBUG:
                return console.debug;
            case LogLevel.INFO:
                return console.info;
            case LogLevel.WARN:
                return console.warn;
            case LogLevel.ERROR:
                return console.error;
            default:
                return console.log;
        }
    }

    /**
     * Log debug message (development only by default)
     */
    debug(message: string, metadata?: LogMetadata): void {
        this.log(LogLevel.DEBUG, message, metadata);
    }

    /**
     * Log info message
     */
    info(message: string, metadata?: LogMetadata): void {
        this.log(LogLevel.INFO, message, metadata);
    }

    /**
     * Log warning message
     */
    warn(message: string, metadata?: LogMetadata): void {
        this.log(LogLevel.WARN, message, metadata);
    }

    /**
     * Log error message
     */
    error(message: string, metadata?: LogMetadata): void {
        this.log(LogLevel.ERROR, message, metadata);
    }

    /**
     * Time a function execution and log the duration
     */
    async time<T>(
        label: string,
        fn: () => Promise<T> | T,
        metadata?: LogMetadata
    ): Promise<T> {
        const start = performance.now();
        try {
            const result = await fn();
            const duration = performance.now() - start;
            this.debug(`${label} completed`, { ...metadata, duration: Math.round(duration) });
            return result;
        } catch (error) {
            const duration = performance.now() - start;
            this.error(`${label} failed`, { ...metadata, error, duration: Math.round(duration) });
            throw error;
        }
    }
}

/**
 * Default logger instance
 */
export const logger = new Logger();

/**
 * Create a logger instance with specific configuration
 */
export const createLogger = (config?: Partial<LoggerConfig>): Logger => {
    return new Logger(config);
};

/**
 * Setup remote logging integration (e.g., Sentry)
 * 
 * Example with Sentry:
 * ```typescript
 * import * as Sentry from '@sentry/nextjs';
 * 
 * setupRemoteLogging((entry) => {
 *   if (entry.level >= LogLevel.ERROR) {
 *     Sentry.captureException(entry.metadata?.error || new Error(entry.message), {
 *       level: entry.levelName.toLowerCase(),
 *       extra: entry.metadata,
 *     });
 *   }
 * });
 * ```
 */
export const setupRemoteLogging = (handler: (entry: LogEntry) => void): void => {
    logger.configure({ remoteHandler: handler });
};

/**
 * Export types for external use
 */
export type { LoggerConfig, LogEntry };
