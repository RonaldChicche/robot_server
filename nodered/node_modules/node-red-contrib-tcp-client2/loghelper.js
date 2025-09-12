class LogHelper {
    constructor(node, level = 'info') {
        this.node = node;
        this.levels = {
            'debug': 1,
            'info': 2,
            'warning': 3,
            'error': 4
        };
        this.currentLevel = this.levels[level];
    }

    setLevel(level) {
        if (this.levels[level] !== undefined) {
            this.currentLevel = this.levels[level];
        } else {
            this.node.error("Invalid logging level.");
        }
    }

    log(message, level = 'info') {
        if (this.levels[level] !== undefined && this.currentLevel <= this.levels[level]) {
            switch(level) {
                case 'error':
                    this.node.error(`[${level.toUpperCase()}]: ${message}`, {});
                    break;
                case 'warning':
                case 'info':
                case 'debug':
                    this.node.warn(`[${level.toUpperCase()}]: ${message}`);
                    break;
                default:
                    // Default action or log for unhandled levels
                    this.node.warn(`[LOG - ${level.toUpperCase()}]: ${message}`);
                    break;
            }
        }
    }

    debug(message) {
        this.log(message, 'debug');
    }

    info(message) {
        this.log(message, 'info');
    }

    warning(message) {
        this.log(message, 'warning');
    }

    error(message) {
        this.log(message, 'error');
    }
}

module.exports = LogHelper;
