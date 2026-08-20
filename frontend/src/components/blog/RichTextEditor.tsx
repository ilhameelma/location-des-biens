import { useCallback, useRef } from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Image from "@tiptap/extension-image";
import Placeholder from "@tiptap/extension-placeholder";
import {
  Bold,
  Italic,
  Underline as UnderlineIcon,
  Strikethrough,
  Heading2,
  Heading3,
  Heading4,
  List,
  ListOrdered,
  Quote,
  Link as LinkIcon,
  ImagePlus,
  Undo,
  Redo,
} from "lucide-react";
import { API_BASE_URL, formatErrorDetail } from "../../lib/api";

/**
 * Éditeur riche pour le contenu des articles de blog.
 *
 * IMPORTANT — la liste des extensions actives ci-dessous est volontairement
 * restreinte pour correspondre EXACTEMENT à la liste blanche appliquée côté
 * serveur (nh3, voir `_TAGS_AUTORISES` dans `backend/app/routers/actualites.py`) :
 * p, br, strong, em, u, s, h2, h3, h4, ul, ol, li, a, img, blockquote.
 * Toute extension ajoutée ici (code, tableau, surlignage...) doit être
 * ajoutée EN MÊME TEMPS côté back, sinon le contenu correspondant est
 * silencieusement retiré à l'enregistrement.
 */

interface RichTextEditorProps {
  content: string;
  onChange: (html: string) => void;
  placeholder?: string;
}

function uploadContenuImage(file: File): Promise<string> {
  const formData = new FormData();
  formData.append("image", file);
  return fetch(`${API_BASE_URL}/actualites/images`, {
    method: "POST",
    credentials: "include",
    body: formData,
  }).then(async (res) => {
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(formatErrorDetail(body.detail, res.status) || `Erreur upload image (${res.status})`);
    }
    const data = (await res.json()) as { url: string };
    return data.url;
  });
}

export default function RichTextEditor({ content, onChange, placeholder }: RichTextEditorProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        // Désactivés : produisent du HTML hors de la liste blanche back
        // (<code>, <pre>, <hr>) — jamais rendu inutilement côté éditeur.
        codeBlock: false,
        code: false,
        horizontalRule: false,
        heading: { levels: [2, 3, 4] },
        link: {
          openOnClick: false,
          autolink: true,
          HTMLAttributes: { rel: "nofollow noopener noreferrer", target: "_blank" },
        },
      }),
      Image.configure({ HTMLAttributes: { class: "rounded-md" } }),
      Placeholder.configure({ placeholder: placeholder ?? "Rédigez votre article…" }),
    ],
    content,
    onUpdate: ({ editor }) => onChange(editor.getHTML()),
    editorProps: {
      attributes: {
        class:
          "min-h-[280px] max-w-none rounded-b-md border border-t-0 border-[var(--color-line)] bg-white px-4 py-3 text-sm leading-relaxed text-[var(--color-ink)] outline-none focus:border-[var(--color-brass)] [&_h2]:mt-4 [&_h2]:font-display [&_h2]:text-xl [&_h3]:mt-3 [&_h3]:font-display [&_h3]:text-lg [&_h4]:mt-2 [&_h4]:font-display [&_h4]:text-base [&_p]:my-2 [&_ul]:my-2 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:my-2 [&_ol]:list-decimal [&_ol]:pl-5 [&_a]:text-[var(--color-brass-deep)] [&_a]:underline [&_blockquote]:border-l-2 [&_blockquote]:border-[var(--color-brass)] [&_blockquote]:pl-3 [&_blockquote]:italic [&_img]:my-2 [&_img]:max-h-80 [&_img]:rounded-md",
      },
    },
  });

  const handleImageButton = useCallback(() => fileInputRef.current?.click(), []);

  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      e.target.value = "";
      if (!file || !editor) return;
      try {
        const url = await uploadContenuImage(file);
        editor.chain().focus().setImage({ src: url }).run();
      } catch (err) {
        window.alert(err instanceof Error ? err.message : "Erreur lors de l'upload de l'image");
      }
    },
    [editor]
  );

  const handleLink = useCallback(() => {
    if (!editor) return;
    const previousUrl = editor.getAttributes("link").href as string | undefined;
    const url = window.prompt("URL du lien", previousUrl ?? "https://");
    if (url === null) return;
    if (url === "") {
      editor.chain().focus().unsetLink().run();
      return;
    }
    editor.chain().focus().setLink({ href: url }).run();
  }, [editor]);

  if (!editor) return null;

  const ToolbarButton = ({
    onClick,
    active,
    label,
    children,
  }: {
    onClick: () => void;
    active?: boolean;
    label: string;
    children: React.ReactNode;
  }) => (
    <button
      type="button"
      title={label}
      aria-label={label}
      onClick={onClick}
      className={`rounded p-1.5 text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)] hover:text-[var(--color-brass-deep)] ${
        active ? "bg-[var(--color-paper-2)] text-[var(--color-brass-deep)]" : ""
      }`}
    >
      {children}
    </button>
  );

  return (
    <div>
      <div className="flex flex-wrap items-center gap-0.5 rounded-t-md border border-[var(--color-line)] bg-[var(--color-paper-2)] px-2 py-1.5">
        <ToolbarButton
          label="Gras"
          active={editor.isActive("bold")}
          onClick={() => editor.chain().focus().toggleBold().run()}
        >
          <Bold size={15} />
        </ToolbarButton>
        <ToolbarButton
          label="Italique"
          active={editor.isActive("italic")}
          onClick={() => editor.chain().focus().toggleItalic().run()}
        >
          <Italic size={15} />
        </ToolbarButton>
        <ToolbarButton
          label="Souligné"
          active={editor.isActive("underline")}
          onClick={() => editor.chain().focus().toggleUnderline().run()}
        >
          <UnderlineIcon size={15} />
        </ToolbarButton>
        <ToolbarButton
          label="Barré"
          active={editor.isActive("strike")}
          onClick={() => editor.chain().focus().toggleStrike().run()}
        >
          <Strikethrough size={15} />
        </ToolbarButton>

        <span className="mx-1 h-5 w-px bg-[var(--color-line)]" />

        <ToolbarButton
          label="Titre 2"
          active={editor.isActive("heading", { level: 2 })}
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
        >
          <Heading2 size={15} />
        </ToolbarButton>
        <ToolbarButton
          label="Titre 3"
          active={editor.isActive("heading", { level: 3 })}
          onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
        >
          <Heading3 size={15} />
        </ToolbarButton>
        <ToolbarButton
          label="Titre 4"
          active={editor.isActive("heading", { level: 4 })}
          onClick={() => editor.chain().focus().toggleHeading({ level: 4 }).run()}
        >
          <Heading4 size={15} />
        </ToolbarButton>

        <span className="mx-1 h-5 w-px bg-[var(--color-line)]" />

        <ToolbarButton
          label="Liste à puces"
          active={editor.isActive("bulletList")}
          onClick={() => editor.chain().focus().toggleBulletList().run()}
        >
          <List size={15} />
        </ToolbarButton>
        <ToolbarButton
          label="Liste numérotée"
          active={editor.isActive("orderedList")}
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
        >
          <ListOrdered size={15} />
        </ToolbarButton>
        <ToolbarButton
          label="Citation"
          active={editor.isActive("blockquote")}
          onClick={() => editor.chain().focus().toggleBlockquote().run()}
        >
          <Quote size={15} />
        </ToolbarButton>

        <span className="mx-1 h-5 w-px bg-[var(--color-line)]" />

        <ToolbarButton label="Lien" active={editor.isActive("link")} onClick={handleLink}>
          <LinkIcon size={15} />
        </ToolbarButton>
        <ToolbarButton label="Insérer une image" onClick={handleImageButton}>
          <ImagePlus size={15} />
        </ToolbarButton>
        <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleFileChange} />

        <span className="mx-1 h-5 w-px bg-[var(--color-line)]" />

        <ToolbarButton label="Annuler" onClick={() => editor.chain().focus().undo().run()}>
          <Undo size={15} />
        </ToolbarButton>
        <ToolbarButton label="Rétablir" onClick={() => editor.chain().focus().redo().run()}>
          <Redo size={15} />
        </ToolbarButton>
      </div>

      <EditorContent editor={editor} />
    </div>
  );
}
