

export class FixedLengthQueue {
    constructor(maxSize) {
        this.queue = [];
        this.maxSize = maxSize;
        this.head = 0;
        this.tail = 0;
        this.size = 0;
    }

    enqueue(item) {
        if (this.isFull()) {
            // drop the oldest one
            this.dequeue();
        }
        this.queue[this.tail] = item;
        this.tail = (this.tail + 1) % this.maxSize;
        this.size++;
    }

    dequeue() {
        if (this.size === 0) {
            throw new Error("Can't dequeue from empty queue");
        }
        const item = this.queue[this.head];
        this.head = (this.head + 1) % this.maxSize;
        this.size--;
        return item;
    }

    peek() {
        if (this.size === 0) {
            return null;
        }
        return this.queue[this.head];
    }

    isEmpty() {
        return this.size === 0;
    }

    isFull() {
        return this.size === this.maxSize;
    }

    get size() {
        return this._size;
    }

    set size(value) {
        this._size = value;
    }
}

export function calc_rate_in_epm(timestamp_queue, current_timestamp, max_age_ms) {
    // remove timestamps older than max age from the queue
    //const beforeSize = timestamp_queue.size;
    while (timestamp_queue.size > 0 && timestamp_queue.peek() + max_age_ms <= current_timestamp) {
        timestamp_queue.dequeue();
    }
    //console.debug('Pruned ' + (beforeSize - timestamp_queue.size)  + ' from timestamp_queue');
    if (timestamp_queue.size === 0) {
        // console.debug('Queue is now empty for calculation. returning 0');
        return 0;
    }
    const peeked_timestamp = timestamp_queue.peek();
    const diff_in_m = (current_timestamp - peeked_timestamp) / (1000 * 60);
    const rate = timestamp_queue.size / diff_in_m;
    const rounded_rate = rate < 1.0 ? Math.round(rate * 10) / 10.0 : Math.round(rate);
    // console.debug('Diff in m: ' + diff_in_m + '; rate: ' + rate + '; rounded rate: ' + rounded_rate);
    return rounded_rate;
}
