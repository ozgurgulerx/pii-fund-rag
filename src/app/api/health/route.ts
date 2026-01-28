import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    status: "ok",
    service: "fund-rag-frontend",
    timestamp: new Date().toISOString(),
  });
}
