/**
 * Modal Component
 * 
 * Reusable modal overlay with backdrop
 * Handles click-outside-to-close functionality
 */

import React from "react";

/* ============================================
   TYPES
   ============================================ */

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  className?: string;
}

/* ============================================
   COMPONENT
   ============================================ */

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  children,
  className = "",
}) => {
  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className={`modal-content ${className}`}
        onClick={(e) => e.stopPropagation()}
      >
        {children}
      </div>
    </div>
  );
};

