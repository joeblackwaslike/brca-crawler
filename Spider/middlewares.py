import time

from scrapy.exceptions import NotConfigured
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.python import global_object_name


class HandleErrors(RetryMiddleware):
    def __init__(self, settings):
        if not settings.getbool("HANDLE_ERRORS_ENABLED"):
            raise NotConfigured
        self.max_retry_times = settings.getint("RETRY_TIMES")
        self.retry_http_codes = set(
            int(x) for x in settings.getlist("RETRY_HTTP_CODES")
        )
        super(HandleErrors, self).__init__(settings)

    def _retry(self, request, reason, spider):
        retries = request.meta.get("retry_times", 0) + 1
        stats = spider.crawler.stats

        spider.logger.debug(
            "Retrying %(request)s (failed %(retries)d times): %(reason)s",
            {"request": request, "retries": retries, "reason": reason},
            extra={"spider": spider},
        )
        retryreq = request.copy()
        retryreq.meta["retry_times"] = retries
        retryreq.dont_filter = True

        if isinstance(reason, Exception):
            reason = global_object_name(reason.__class__)

        stats.inc_value("retry/count")
        stats.inc_value("retry/reason_count/%s" % reason)

        current_folio = request.meta["state"].current_folio
        spider.logger.info(
            "error: %s on folio %s, backing off %s seconds",
            reason,
            current_folio,
            retries,
        )
        time.sleep(1 * retries)
        return retryreq
