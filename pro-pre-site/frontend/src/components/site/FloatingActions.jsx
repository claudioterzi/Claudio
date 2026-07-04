import React from "react";
import { MessageCircle, Phone } from "lucide-react";
import { BRAND } from "@/lib/api";

export default function FloatingActions() {
  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-3" data-testid="floating-actions">
      <a
        href={`https://wa.me/${BRAND.whatsapp.replace(/[^0-9]/g,'')}`}
        target="_blank" rel="noreferrer"
        className="flex h-14 w-14 items-center justify-center rounded-full bg-[#25D366] text-white shadow-xl hover:scale-105 transition-transform"
        data-testid="floating-whatsapp"
        aria-label="WhatsApp"
      >
        <MessageCircle className="h-6 w-6" />
      </a>
      <a
        href={`tel:${BRAND.phone}`}
        className="flex h-14 w-14 items-center justify-center rounded-full bg-[#1B2845] text-white shadow-xl hover:scale-105 transition-transform"
        data-testid="floating-call"
        aria-label="Call"
      >
        <Phone className="h-6 w-6" />
      </a>
    </div>
  );
}
