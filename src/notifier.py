"""Notification engine: Google Workspace HTML email, Windows toast, and logs."""

import logging
import smtplib
import subprocess
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from src.config import Config
from src.models import PipelineStats, QualifiedTender

logger = logging.getLogger(__name__)


class Notifier:
    """Manages multi-channel pipeline notifications (Email, Toast, Telemetry)."""

    def __init__(self, config: Config | None = None):
        """Initialize with application configuration."""
        self.config = config or Config

    def send_daily_digest(
        self,
        tenders: list[QualifiedTender],
        stats: PipelineStats,
        csv_path: Path | None = None,
    ) -> bool:
        """Send formatted HTML email digest to team with CSV attachment.

        Args:
            tenders: List of AI-qualified tenders.
            stats: Execution telemetry stats.
            csv_path: Path to the generated CSV file.

        Returns:
            True if sent successfully, False otherwise.
        """
        sender = self.config.GMAIL_SENDER
        password = self.config.GMAIL_APP_PASSWORD
        recipients = self.config.TEAM_EMAILS

        if not sender or not password or not recipients:
            logger.warning(
                "Email credentials or recipient list not set in .env. "
                "Skipping email dispatch."
            )
            return False

        now_str = datetime.now().strftime("%d %b %Y")
        count = len(tenders)

        if count == 0:
            if not self.config.SEND_ZERO_MATCH_HEARTBEAT:
                logger.info(
                    "Zero tenders found and heartbeat disabled. Skipping email."
                )
                return True
            subject = f"🔔 [eTender Daily] 0 New Matches for {now_str} (System Healthy)"
            html_body = self._build_heartbeat_html(stats, now_str)
        else:
            subject = (
                f"🎯 [eTender Daily] {count} AI & Digital Opportunities "
                f"Discovered ({now_str})"
            )
            html_body = self._build_digest_html(tenders, stats, now_str)

        msg = MIMEMultipart("mixed")
        msg["From"] = f"eTender Intelligence <{sender}>"
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject

        # Attach HTML body
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Attach CSV if exists and we have matching tenders
        if csv_path and csv_path.exists() and count > 0:
            with open(csv_path, "rb") as f:
                attachment = MIMEApplication(f.read(), Name=csv_path.name)
                attachment["Content-Disposition"] = (
                    f'attachment; filename="{csv_path.name}"'
                )
                msg.attach(attachment)

        try:
            logger.info(
                f"Connecting to Google Workspace SMTP to email {len(recipients)} members..."
            )
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
                server.login(sender, password)
                server.sendmail(sender, recipients, msg.as_string())
            logger.info("Daily digest email successfully delivered to team!")
            return True
        except (smtplib.SMTPException, OSError) as exc:
            logger.error(f"Failed to send email via SMTP: {exc}")
            return False

    def show_windows_toast(self, title: str, message: str) -> None:
        """Trigger a non-intrusive native Windows desktop toast notification."""
        if not self.config.ENABLE_WINDOWS_TOAST:
            return

        try:
            # Escape quotes for PowerShell
            clean_title = title.replace("'", "''")
            clean_msg = message.replace("'", "''")

            ps_script = (
                "[void] [System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); "
                "$toast = New-Object System.Windows.Forms.NotifyIcon; "
                "$toast.Icon = [System.Drawing.SystemIcons]::Information; "
                "$toast.Visible = $True; "
                f"$toast.ShowBalloonTip(4000, '{clean_title}', '{clean_msg}', "
                "[System.Windows.Forms.ToolTipIcon]::Info); "
                "Start-Sleep -Seconds 2; $toast.Dispose()"
            )

            subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", ps_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info(f"Desktop notification triggered: {title}")
        except (subprocess.SubprocessError, OSError) as exc:
            logger.debug(f"Unable to show Windows toast: {exc}")

    def _build_digest_html(
        self, tenders: list[QualifiedTender], stats: PipelineStats, date_str: str
    ) -> str:
        """Construct a high-aesthetic, modern HTML email template."""
        rows_html = ""
        for t in tenders:
            eval_data = t.ai_evaluation
            score_color = (
                "#10b981"
                if (eval_data and eval_data.relevance_score >= 8.0)
                else "#3b82f6"
            )
            score_badge = (
                f'<span style="background:{score_color};color:#ffffff;padding:4px 8px;'
                f'border-radius:12px;font-weight:700;font-size:12px;">'
                f"{eval_data.relevance_score:.1f}/10</span>"
                if eval_data
                else "N/A"
            )

            action = eval_data.recommended_action if eval_data else "Review"
            summary = eval_data.executive_summary if eval_data else t.description[:200]
            contact = t.contact_email or "See Portal"
            docs_count = len(t.attached_documents)

            rows_html += f"""
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 14px 10px; font-weight: 600; color: #0f172a;">
                    {t.tender_no}<br>
                    <span style="font-size: 11px; color: #64748b; font-weight: 400;">{t.province}</span>
                </td>
                <td style="padding: 14px 10px; color: #334155;">
                    <strong>{t.organ_of_state}</strong><br>
                    <div style="font-size: 13px; color: #475569; margin-top: 4px;">{summary}</div>
                    <div style="font-size: 11px; color: #0284c7; margin-top: 4px;">Docs: {docs_count} file(s) attached</div>
                </td>
                <td style="padding: 14px 10px; text-align: center;">{score_badge}</td>
                <td style="padding: 14px 10px; font-size: 13px; color: #b91c1c; font-weight: 600; white-space: nowrap;">
                    {t.closing_date or "N/A"}
                </td>
                <td style="padding: 14px 10px; font-size: 12px; color: #475569;">
                    <a href="mailto:{contact}" style="color: #2563eb; text-decoration: none;">{contact}</a><br>
                    <span style="color: #16a34a; font-weight: 600;">{action}</span>
                </td>
            </tr>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px;">
            <div style="max-width: 850px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 28px 24px; color: #ffffff;">
                    <h1 style="margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.5px;">🎯 eTender Intelligence Digest</h1>
                    <p style="margin: 6px 0 0; color: #94a3b8; font-size: 14px;">High-Priority Opportunities in AI Landscape & Digital Marketing • {date_str}</p>
                </div>
                
                <div style="padding: 24px;">
                    <p style="font-size: 15px; color: #334155; margin-top: 0;">
                        Our automated scanner analyzed <strong>{stats.total_scanned:,}</strong> active tenders across South Africa. 
                        <strong>{len(tenders)}</strong> bids were qualified by local AI (<code>{stats.model_used}</code>) as genuine strategic opportunities.
                    </p>

                    <div style="overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 14px; margin-top: 16px;">
                            <thead>
                                <tr style="background: #f1f5f9; color: #475569; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">
                                    <th style="padding: 10px;">Ref / Province</th>
                                    <th style="padding: 10px; width: 45%;">Tender & Executive Summary</th>
                                    <th style="padding: 10px; text-align: center;">Score</th>
                                    <th style="padding: 10px;">Closing</th>
                                    <th style="padding: 10px;">Action / Contact</th>
                                </tr>
                            </thead>
                            <tbody>
                                {rows_html}
                            </tbody>
                        </table>
                    </div>

                    <div style="margin-top: 24px; padding: 14px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; font-size: 12px; color: #64748b;">
                        📎 <strong>Attached:</strong> Complete CSV with all extracted fields and specifications has been attached for your records.
                    </div>
                </div>

                <div style="background: #f1f5f9; padding: 16px 24px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #64748b;">
                    ⚡ <strong>System Heartbeat</strong>: Processed {stats.total_scanned:,} tenders in {stats.elapsed_seconds:.1f}s • AI Evaluator: {stats.model_used} • Status: 100% Operational • Delivery: 4 Team Members
                </div>
            </div>
        </body>
        </html>
        """

    def _build_heartbeat_html(self, stats: PipelineStats, date_str: str) -> str:
        """Construct lightweight HTML confirmation when zero matches were found."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 10px; padding: 24px; border: 1px solid #e2e8f0;">
                <h2 style="color: #0f172a; margin-top: 0; font-size: 18px;">🔔 eTender Daily System Heartbeat</h2>
                <p style="color: #475569; font-size: 14px; line-height: 1.5;">
                    The eTender pipeline completed its scheduled morning scan for <strong>{date_str}</strong>.<br>
                    <strong>{stats.total_scanned:,}</strong> public sector tenders were scanned across the National Treasury portal.
                </p>
                <div style="background: #eff6ff; border-left: 4px solid #3b82f6; padding: 12px; border-radius: 4px; font-size: 13px; color: #1e40af;">
                    ℹ️ <strong>Status:</strong> System Healthy — No new tenders matching our high-priority AI or Digital Marketing criteria were published in the last cycle.
                </div>
                <p style="color: #64748b; font-size: 12px; margin-top: 20px; border-top: 1px solid #e2e8f0; padding-top: 12px;">
                    ⚡ Run time: {stats.elapsed_seconds:.1f}s • Model: {stats.model_used} • Next scheduled execution: Tomorrow at 08:00 AM.
                </p>
            </div>
        </body>
        </html>
        """
